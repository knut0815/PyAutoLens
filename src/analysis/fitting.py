import numpy as np

from src.imaging import grids
from src.analysis import ray_tracing
from src.pixelization import pixelization as px


# TODO : Can we make model_immage, galaxy_images, minimum_Values a part of hyper galaxies?

def fit_data_with_profiles_hyper_galaxies(image, kernel_convolver, tracer, mapping, model_image, galaxy_images,
                                          minimum_values, hyper_galaxies):
    """Fit the weighted_data using the ray_tracing model, where only light_profiles are used to represent the galaxy images.

    Parameters
    ----------
    image
    grid_data : grids.DataCollection
        The collection of grid weighted_data-sets (image, noise, etc.)
    kernel_convolver : auto_lens.pixelization.frame_convolution.KernelConvolver
        The 2D Point Spread Function (PSF).
    tracer : ray_tracing.Tracer
        The ray-tracing configuration of the model galaxies and their profiles.
    model_image : ndarray
        The best-fit model image to the weighted_data, from a previous phase of the pipeline
    galaxy_images : [ndarray]
        The best-fit model image of each hyper-galaxy, which can tell us how much flux each pixel contributes to.
    hyper_galaxies : [galaxy.HyperGalaxy]
        Each hyper-galaxy which is used to determine its contributions.
    """
    contributions = generate_contributions(model_image, galaxy_images, hyper_galaxies, minimum_values)
    scaled_noise = generate_scaled_noise(image.background_noise, contributions, hyper_galaxies)
    blurred_model_image = generate_blurred_light_profile_image(tracer, kernel_convolver, mapping)
    return compute_likelihood(image, scaled_noise, blurred_model_image)


def generate_contributions(model_image, galaxy_images, hyper_galaxies, minimum_values):
    """Use the model image and galaxy image (computed in the previous phase of the pipeline) to determine the
    contributions of each hyper galaxy.

    Parameters
    -----------
    minimum_values
    model_image : ndarray
        The best-fit model image to the weighted_data, from a previous phase of the pipeline
    galaxy_images : [ndarray]
        The best-fit model image of each hyper-galaxy, which can tell us how much flux each pixel contributes to.
    hyper_galaxies : [galaxy.HyperGalaxy]
        Each hyper-galaxy which is used to determine its contributions.
    """
    return list(map(lambda hyper, galaxy_image, minimum_value:
                    hyper.compute_contributions(model_image, galaxy_image, minimum_value),
                    hyper_galaxies, galaxy_images, minimum_values))


def generate_scaled_noise(noise, contributions, hyper_galaxies):
    """Use the contributions of each hyper galaxy to compute the scaled noise.

    Parameters
    -----------
    noise : grids.GridData
        The (unscaled) noise in each pixel.
    contributions : [ndarray]
        The contribution of flux of each galaxy in each pixel (computed from galaxy.HyperGalaxy)
    hyper_galaxies : [galaxy.HyperGalaxy]
        Each hyper-galaxy which is used to scale the noise.
    """
    scaled_noises = list(map(lambda hyper, contribution: hyper.compute_scaled_noise(noise, contribution),
                             hyper_galaxies, contributions))

    return noise + sum(scaled_noises)


def fit_data_with_profiles(image, kernel_convolver, tracer, mapping):
    """Fit the weighted_data using the ray_tracing model, where only light_profiles are used to represent the galaxy images.

    Parameters
    ----------
    image
    kernel_convolver : auto_lens.pixelization.frame_convolution.KernelConvolver
        The 2D Point Spread Function (PSF).
    tracer : ray_tracing.Tracer
        The ray-tracing configuration of the model galaxies and their profiles.
    mapping : grids.GridMapping
        Contains arrays / functions used to map different grids.
    """
    blurred_model_image = generate_blurred_light_profile_image(tracer, kernel_convolver, mapping)
    return compute_likelihood(image, image.background_noise, blurred_model_image)


def generate_blurred_light_profile_image(tracer, kernel_convolver, mapping):
    """For a given ray-tracing model, compute the light profile image(s) of its galaxies and blur them with the
    PSF.

    Parameters
    ----------
    mapping
    tracer : ray_tracing.Tracer
        The ray-tracing configuration of the model galaxies and their profiles.
    kernel_convolver : auto_lens.pixelization.frame_convolution.KernelConvolver
        The 2D Point Spread Function (PSF).
    """
    image_light_profile = tracer.generate_image_of_galaxy_light_profiles(mapping)
    blurring_image_light_profile = tracer.generate_blurring_image_of_galaxy_light_profiles()
    return blur_image_including_blurring_region(image_light_profile, blurring_image_light_profile, kernel_convolver)


def blur_image_including_blurring_region(image, blurring_image, kernel_convolver):
    """For a given image and blurring region, convert them to 2D and blur with the PSF, then return as the 1D DataGrid.

    Parameters
    ----------
    image : ndarray
        The image weighted_data using the GridData 1D representation.
    blurring_image : ndarray
        The blurring region weighted_data, using the GridData 1D representation.
    kernel_convolver : auto_lens.pixelization.frame_convolution.KernelConvolver
        The 2D Point Spread Function (PSF).
    """
    return kernel_convolver.convolve_array(image, blurring_image)


def fit_data_with_pixelization(image, kernel_convolver, tracer, mapping):
    """Fit the weighted_data using the ray_tracing model, where only pixelizations are used to represent the galaxy
    images.

    Parameters
    ----------
    mapping
    image
    kernel_convolver : auto_lens.pixelization.frame_convolution.KernelConvolver
        The 2D Point Spread Function (PSF).
    tracer : ray_tracing.Tracer
        The ray-tracing configuration of the model galaxies and their profiles.

    """

    pix_pre_fit = tracer.generate_pixelization_matrices_of_source_galaxy(mapping)
    pix_fit = pix_pre_fit.fit_image_via_inversion(image, image.background_noise, kernel_convolver)

    model_image = pix_fit.model_image_from_reconstruction()

    return compute_pixelization_evidence(image, image.background_noise, model_image, pix_fit)


def compute_likelihood(image, noise, model_image):
    """Compute the likelihood of a model image's fit to the weighted_data, by taking the difference between the observed
    image and model ray-tracing image. The likelihood consists of two terms:

    Chi-squared term - The residuals (model - weighted_data) of every pixel divided by the noise in each pixel, all
    squared.
    [Chi_Squared_Term] = sum(([Residuals] / [Noise]) ** 2.0)

    The overall normalization of the noise is also included, by summing the log noise value in each pixel:
    [Noise_Term] = sum(log(2*pi*[Noise]**2.0))

    These are summed and multiplied by -0.5 to give the likelihood:

    Likelihood = -0.5*[Chi_Squared_Term + Noise_Term]

    Parameters
    ----------
    image : grids.GridData
        The image weighted_data.
    noise : grids.GridData
        The noise in each pixel.
    model_image : grids.GridData
        The model image of the weighted_data.
    """
    return -0.5 * (compute_chi_sq_term(image, noise, model_image) + compute_noise_term(noise))


def compute_pixelization_evidence(image, noise, model_image, pix_fit):
    return -0.5 * (compute_chi_sq_term(image, noise, model_image)
                   + pix_fit.regularization_term_from_reconstruction()
                   + pix_fit.log_determinant_of_matrix_cholesky(pix_fit.covariance_regularization)
                   - pix_fit.log_determinant_of_matrix_cholesky(pix_fit.regularization)
                   + compute_noise_term(noise))


def compute_chi_sq_term(image, noise, model_image):
    """Compute the chi-squared of a model image's fit to the weighted_data, by taking the difference between the observed \
    image and model ray-tracing image, dividing by the noise in each pixel and squaring:

    [Chi_Squared] = sum(([Data - Model] / [Noise]) ** 2.0)

    Parameters
    ----------
    image : grids.GridData
        The image weighted_data.
    noise : grids.GridData
        The noise in each pixel.
    model_image : grids.GridData
        The model image of the weighted_data.
    """
    return np.sum((np.add(image.view(float), - model_image) / noise) ** 2.0)


def compute_noise_term(noise):
    """Compute the noise normalization term of an image, which is computed by summing the noise in every pixel:

    [Noise_Term] = sum(log(2*pi*[Noise]**2.0))

    Parameters
    ----------
    noise : grids.GridData
        The noise in each pixel.
    """
    return np.sum(np.log(2 * np.pi * noise ** 2.0))


def fit_data_with_pixelization_and_profiles(grid_data_collection, pixelization, kernel_convolver, tracer,
                                            mapper_cluster, image=None):
    # TODO: Implement me
    raise NotImplementedError("fit_data_with_pixelization_and_profiles has not been implemented")
