# %%
"""
Tutorial 3: Complex Source
==========================

Up to now, we've not paid much attention to the source-galaxy's morphology. We've assumed its a single-component
exponential profile, which is a fairly crude assumption. A quick look at any image of a real galaxy reveals a
wealth of different structures that could be present - bulges, disks, bars, star-forming knots and so on. Furthermore,
there could be more than one source-galaxy!

In this example, we'll explore how far we can get trying to_fit a complex source using a pipeline. Fitting complex
source's is an exercise in diminishing returns. Each component we add to our source model brings with it an
extra 5-7, parameters. If there are 4 components, or multiple _Galaxy_'s we're quickly entering the somewhat nasty
regime of 30-40+ parameters in our non-linear search. Even with a pipeline, that is a lot of parameters to fit!
"""

# %%
""" AUTOFIT + CONFIG SETUP """

# %%
from autoconf import conf
import os

workspace_path = os.environ["WORKSPACE"]
print("Workspace Path: ", workspace_path)

conf.instance = conf.Config(
    config_path=f"{workspace_path}/howtolens/config",
    output_path=f"{workspace_path}/howtolens/output",
)

# %%
#%matplotlib inline

import autolens as al
import autolens.plot as aplt

# %%
"""
We'll use new strong lensing data, where:

 - The lens galaxy's light is omitted.
 - The lens galaxy's _MassProfile_ is an _EllipticalIsothermal_.
 - The source galaxy's _LightProfile_ is four _EllipticalSersic_'s.
"""

# %%
from howtolens.simulators.chapter_3 import mass_sie__source_sersic_x4

dataset_type = "chapter_3"
dataset_name = "mass_sie__source_sersic_x4"
dataset_path = f"{workspace_path}/howtolens/dataset/{dataset_type}/{dataset_name}"

imaging = al.Imaging.from_fits(
    image_path=f"{dataset_path}/image.fits",
    noise_map_path=f"{dataset_path}/noise_map.fits",
    psf_path=f"{dataset_path}/psf.fits",
    pixel_scales=0.1,
)

# %%
"""
We need to choose our mask for the analysis. Given the lens light is present in the image we'll need to include all 
of its light in the central regions of the image, so lets use a circular mask.
"""

# %%
mask = al.Mask2D.circular(
    shape_2d=imaging.shape_2d, pixel_scales=imaging.pixel_scales, radius=3.0
)

aplt.Imaging.subplot_imaging(imaging=imaging, mask=mask)

# %%
"""
Yep, that's a pretty complex source. There are clearly more than 4 peaks of light - I wouldn't like to guess how many
sources of light there truly is! You'll also notice I omitted the lens galaxy's light for this system. This is to 
keep the number of parameters down and the phases running fast, but we wouldn't get such a luxury for a real galaxy.
"""

# %%
"""
__Settings__

The _SettingsPhaseImaging_ describe how the model is fitted to the data in the log likelihood function. We discussed
these in chapter 2, and a full description of all settings can be found in the example script:

 'autolens_workspace/examples/model/customize/settings.py'.

The settings chosen here are applied to all phases in the pipeline.
"""

# %%
settings_masked_imaging = al.SettingsMaskedImaging(grid_class=al.Grid, sub_size=2)

settings = al.SettingsPhaseImaging(settings_masked_imaging=settings_masked_imaging)

# %%
"""
__Pipeline_Setup_And_Tagging__:

For this pipeline the pipeline setup customizes:

 - If there is an _ExternalShear_ in the mass model or not.
"""

# %%
setup_mass = al.SetupMassTotal(no_shear=False)
setup_source = al.SetupSourceSersic()

setup = al.SetupPipeline(
    folders=["c3_t3_complex_source"],
    redshift_lens=0.5,
    redshift_source=1.0,
    setup_mass=setup_mass,
    setup_source=setup_source,
)

# %%
"""
__Pipeline Creation__

To create a _Pipeline_, we call a 'make_pipeline' function, which is written in its own Python script: 

 'tutorial_3_complex_source.py'. 

Before we check it out, lets get the pipeline running, by importing the script, running the 'make_pipeline' function
to create the _Pipeline_ object and calling that objects 'run' function.

The 'folders' below specify the path the pipeline results are written to, which is:

 'autolens_workspace/output/howtolens/c3_t3_complex_source/pipeline_name/setup_tag/phase_name/settings_tag'
"""

# %%
from howtolens.chapter_3_pipelines import tutorial_3_pipeline_complex_source

pipeline_complex_source = tutorial_3_pipeline_complex_source.make_pipeline(
    setup=setup, settings=settings
)

# Uncomment to run.
# pipeline_complex_source.run(dataset=imaging, mask=mask)

# %%
"""
Okay, so with 4 sources, we still couldn't get a good a fit to the source that didn't leave residuals. However, I 
actually simulated the lens with 4 sources. This means that there is a 'perfect fit' somewhere in parameter space 
that we unfortunately missed using the pipeline above.

Lets confirm this, by manually fitting the _Imaging_ data with the true input model.
"""

# %%
masked_imaging = al.MaskedImaging(
    imaging=imaging,
    mask=al.Mask2D.circular(
        shape_2d=imaging.shape_2d, pixel_scales=imaging.pixel_scales, radius=3.0
    ),
)

lens_galaxy = al.Galaxy(
    redshift=0.5,
    mass=al.mp.EllipticalIsothermal(
        centre=(0.0, 0.0), elliptical_comps=(0.1, 0.0), einstein_radius=1.6
    ),
)

source_galaxy_0 = al.Galaxy(
    redshift=1.0,
    sersic=al.lp.EllipticalSersic(
        centre=(0.1, 0.1),
        elliptical_comps=(0.0, 0.1),
        intensity=0.2,
        effective_radius=1.0,
        sersic_index=1.5,
    ),
)

source_galaxy_1 = al.Galaxy(
    redshift=1.0,
    sersic=al.lp.EllipticalSersic(
        centre=(-0.25, 0.25),
        elliptical_comps=(0.0, 0.15),
        intensity=0.1,
        effective_radius=0.2,
        sersic_index=3.0,
    ),
)

source_galaxy_2 = al.Galaxy(
    redshift=1.0,
    sersic=al.lp.EllipticalSersic(
        centre=(0.45, -0.35),
        elliptical_comps=(0.0, 0.222222),
        intensity=0.03,
        effective_radius=0.3,
        sersic_index=3.5,
    ),
)

source_galaxy_3 = al.Galaxy(
    redshift=1.0,
    sersic=al.lp.EllipticalSersic(
        centre=(-0.05, -0.0),
        elliptical_comps=(0.0, 0.15),
        intensity=0.03,
        effective_radius=0.1,
        sersic_index=4.0,
    ),
)

tracer = al.Tracer.from_galaxies(
    galaxies=[
        lens_galaxy,
        source_galaxy_0,
        source_galaxy_1,
        source_galaxy_2,
        source_galaxy_3,
    ]
)

true_fit = al.FitImaging(masked_imaging=masked_imaging, tracer=tracer)

aplt.FitImaging.subplot_fit_imaging(fit=true_fit)

aplt.FitImaging.subplot_of_plane(fit=true_fit, plane_index=1)


# %%
"""
And indeed, we see an improved residual-map, chi-squared-map, and so forth.

The morale of this story is that if the source morphology is complex, there is no way we can build a pipeline to 
fit it. For this tutorial, this was true even though our source model could actually fit the data perfectly. For real 
lenses, the source will be *even more complex* and there is even less hope of getting a good fit :(

But fear not, __PyAutoLens__ has you covered. In chapter 4, we'll introduce a completely new way to model the source 
galaxy, which addresses the problem faced here. But before that, in the next tutorial we'll discuss how we actually 
pass priors in a pipeline.
"""
