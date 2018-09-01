import numpy as np
from autolens.imaging import imaging_util
from autolens.imaging import image
from autolens.imaging import mask
from autolens.lensing import grids
import pytest


@pytest.fixture(name="msk")
def make_mask():
    return mask.Mask(np.array([[True, False, True],
                               [False, False, False],
                               [True, False, True]]))


@pytest.fixture(name="centre_mask")
def make_centre_mask():
    return mask.Mask(np.array([[True, True, True],
                               [True, False, True],
                               [True, True, True]]))


@pytest.fixture(name="sub_grid")
def make_sub_grid(msk):
    return grids.SubGrid.grid_from_mask_and_sub_grid_size(msk, sub_grid_size=1)

@pytest.fixture(name="lensing_grids")
def make_lensing_grids(centre_mask):
    return grids.LensingGrids.from_mask_sub_grid_size_and_blurring_shape(centre_mask, 2, (3, 3))


class TestImageGrid:

    def test__compute_xticks_property__include_round_to_2dp(self):

        grid = grids.ImageGrid(arr=np.array([[0.0, 0.0], [0.0, 0.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.xticks == pytest.approx(np.array([-0.3, -0.1, 0.1, 0.3]), 1e-3)

        grid = grids.ImageGrid(arr=np.array([[-6.0, -10.5], [6.0, 0.5], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.xticks == pytest.approx(np.array([-6.0, -2.0, 2.0, 6.0]), 1e-3)

        grid = grids.ImageGrid(arr=np.array([[-1.0, -0.5], [1.0, 0.5], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.xticks == pytest.approx(np.array([-1.0, -0.33, 0.33, 1.0]), 1e-3)

    def test__compute_yticks_property__include_round_to_2dp(self):

        grid = grids.ImageGrid(arr=np.array([[0.0, 0.0], [0.0, 0.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.yticks == pytest.approx(np.array([-0.3, -0.1, 0.1, 0.3]), 1e-3)

        grid = grids.ImageGrid(arr=np.array([[-10.5, -6.0], [0.5, 6.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.yticks == pytest.approx(np.array([-6.0, -2.0, 2.0, 6.0]), 1e-3)

        grid = grids.ImageGrid(arr=np.array([[-0.5, -1.0], [0.5, 1.0], [0.3, 0.3], [-0.3, -0.3]]))
        assert grid.yticks == pytest.approx(np.array([-1.0, -0.33, 0.33, 1.0]), 1e-3)

    def test__blurring_grid_from_mask__compare_to_array_util(self):

        msk = np.array([[True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, False, True, True, True, False, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, False, True, True, True, False, True, True],
                        [True, True, True, True, True, True, True, True, True],
                        [True, True, True, True, True, True, True, True, True]])

        blurring_mask_util = imaging_util.mask_blurring_from_mask_and_psf_shape(msk, psf_shape=(3, 5))
        blurring_grid_util = imaging_util.image_grid_masked_from_mask_and_pixel_scale(blurring_mask_util, pixel_scale=2.0)

        msk = mask.Mask(msk, pixel_scale=2.0)
        blurring_grid = grids.ImageGrid.blurring_grid_from_mask_and_psf_shape(mask=msk, psf_shape=(3,5))

        assert blurring_grid == pytest.approx(blurring_grid_util, 1e-4)


class TestSubGrid(object):

    def test_sub_grid(self, sub_grid):
        assert sub_grid.shape == (5, 2)
        assert (sub_grid == np.array([[-1, 0], [0, -1], [0, 0], [0, 1], [1, 0]])).all()

    def test_sub_to_pixel(self, sub_grid):
        assert (sub_grid.sub_to_image == np.array(range(5))).all()

    def test__from_mask(self):

        msk = np.array([[True, True, True],
                        [True, False, False],
                        [True, True, False]])

        sub_grid_util = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask=msk, pixel_scale=3.0,
                                                                                             sub_grid_size=2)

        msk = mask.Mask(msk, pixel_scale=3.0)

        sub_grid = grids.SubGrid.grid_from_mask_and_sub_grid_size(msk, sub_grid_size=2)

        assert sub_grid == pytest.approx(sub_grid_util, 1e-4)

    def test_sub_data_to_image(self, sub_grid):
        assert (sub_grid.sub_data_to_image(np.array(range(5))) == np.array(range(5))).all()

    def test_sub_to_image__compare_to_array_util(self):

        msk = np.array([[True, False, True],
                        [False, False, False],
                        [True, False, False]])

        sub_to_image_util = imaging_util.sub_to_image_from_mask(msk, sub_grid_size=2)

        msk = mask.Mask(msk, pixel_scale=3.0)

        sub_grid = grids.SubGrid.grid_from_mask_and_sub_grid_size(mask=msk, sub_grid_size=2)
        assert sub_grid.sub_grid_size == 2
        assert sub_grid.sub_grid_fraction == (1.0 / 4.0)
        assert (sub_grid.sub_to_image == sub_to_image_util).all()


class TestGridsMappers:


    class TestImageMapperFromShapes:

        def test__3x3_array__psf_size_is_1x1__no_padding(self):

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(3, 3), psf_shape=(1,1),
                                                                                 pixel_scale=1.0)

            assert len(image_mapper) == 9
            assert image_mapper.original_shape == (3, 3)
            assert image_mapper.padded_shape == (3, 3)

        def test__3x3_image__5x5_psf_size__7x7_image_mapper_made(self):

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(3, 3), psf_shape=(5,5),
                                                                                 pixel_scale=1.0)

            assert len(image_mapper) == 49
            assert image_mapper.original_shape == (3, 3)
            assert image_mapper.padded_shape == (7, 7)

        def test__3x3_image__7x7_psf_size__9x9_image_mapper_made(self):

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(3, 3), psf_shape=(7,7),
                                                                                 pixel_scale=1.0)
            assert len(image_mapper) == 81
            assert image_mapper.original_shape == (3, 3)
            assert image_mapper.padded_shape == (9, 9)

        def test__4x3_image__3x3_psf_size__6x5_image_mapper_made(self):

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(4, 3), psf_shape=(3,3),
                                                                                 pixel_scale=1.0)
            assert len(image_mapper) == 30
            assert image_mapper.original_shape == (4, 3)
            assert image_mapper.padded_shape == (6, 5)

        def test__3x4_image__3x3_psf_size__5x6_image_mapper_made(self):

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(3, 4), psf_shape=(3,3),
                                                                                 pixel_scale=1.0)

            assert len(image_mapper) == 30
            assert image_mapper.original_shape == (3, 4)
            assert image_mapper.padded_shape == (5, 6)

        def test__4x4_image__3x3_psf_size__6x6_image_mapper_made(self):

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(4, 4), psf_shape=(3,3),
                                                                                 pixel_scale=1.0)

            assert len(image_mapper) == 36
            assert image_mapper.original_shape == (4, 4)
            assert image_mapper.padded_shape == (6, 6)

        def test__image_mapper_coordinates__match_grid_2d_after_padding(self):

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(4, 4), psf_shape=(3,3),
                                                                                 pixel_scale=3.0)

            image_mapper_util = imaging_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((6, 6), False),
                                                                                  pixel_scale=3.0)
            assert (image_mapper == image_mapper_util).all()
            assert image_mapper.original_shape == (4, 4)
            assert image_mapper.padded_shape == (6, 6)

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(4, 5), psf_shape=(3,3),
                                                                                 pixel_scale=2.0)
            image_mapper_util = imaging_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((6, 7), False),
                                                                                  pixel_scale=2.0)
            assert (image_mapper == image_mapper_util).all()
            assert image_mapper.original_shape == (4, 5)
            assert image_mapper.padded_shape == (6, 7)

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(5, 4), psf_shape=(3,3),
                                                                                 pixel_scale=1.0)
            image_mapper_util = imaging_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((7, 6), False),
                                                                                  pixel_scale=1.0)
            assert (image_mapper == image_mapper_util).all()
            assert image_mapper.original_shape == (5, 4)
            assert image_mapper.padded_shape == (7, 6)

            image_mapper = grids.ImageGridMapper.mapper_from_shapes_and_pixel_scale(shape=(2, 5), psf_shape=(5,5),
                                                                                 pixel_scale=8.0)
            image_mapper_util = imaging_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((6, 9), False),
                                                                                  pixel_scale=8.0)
            assert (image_mapper == image_mapper_util).all()
            assert image_mapper.original_shape == (2, 5)
            assert image_mapper.padded_shape == (6, 9)


    class TestSubMapperFromMask:

        def test__3x3_array__psf_size_is_1x1__no_padding(self):

            msk = mask.Mask(array=np.full((3, 3), False), pixel_scale=1.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=3,
                                                                                       psf_shape=(1, 1))

            assert len(sub_mapper) == 9 * 3 ** 2
            assert sub_mapper.original_shape == (3, 3)
            assert sub_mapper.padded_shape == (3, 3)

        def test__3x3_image__5x5_psf_size__7x7_image_grid_made(self):

            msk = mask.Mask(array=np.full((3, 3), False), pixel_scale=1.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=2,
                                                                                       psf_shape=(5, 5))

            assert len(sub_mapper) == 49 * 2 ** 2
            assert sub_mapper.original_shape == (3, 3)
            assert sub_mapper.padded_shape == (7, 7)

        def test__4x3_image__3x3_psf_size__6x5_image_grid_made(self):

            msk = mask.Mask(array=np.full((4, 3), False), pixel_scale=1.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=2,
                                                                                       psf_shape=(3, 3))

            assert len(sub_mapper) == 30 * 2 ** 2
            assert sub_mapper.original_shape == (4, 3)
            assert sub_mapper.padded_shape == (6, 5)

        def test__3x4_image__3x3_psf_size__5x6_image_grid_made(self):

            msk = mask.Mask(array=np.full((3, 4), False), pixel_scale=1.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=2,
                                                                                       psf_shape=(3, 3))

            assert len(sub_mapper) == 30 * 2 ** 2
            assert sub_mapper.original_shape == (3, 4)
            assert sub_mapper.padded_shape == (5, 6)

        def test__4x4_image__3x3_psf_size__6x6_image_grid_made(self):

            msk = mask.Mask(array=np.full((4, 4), False), pixel_scale=1.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=4,
                                                                                       psf_shape=(3, 3))

            assert len(sub_mapper) == 36 * 4 ** 2
            assert sub_mapper.original_shape == (4, 4)
            assert sub_mapper.padded_shape == (6, 6)

        def test__sub_mapper_coordinates__match_grid_2d_after_padding(self):

            msk = mask.Mask(array=np.full((4, 4), False), pixel_scale=3.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=3,
                                                                                       psf_shape=(3, 3))

            sub_mapper_util = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(
                mask=np.full((6, 6), False), pixel_scale=3.0, sub_grid_size=3)

            assert (sub_mapper == sub_mapper_util).all()

            msk = mask.Mask(array=np.full((4, 5), False), pixel_scale=2.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=1,
                                                                                       psf_shape=(3, 3))

            sub_mapper_util = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(
                mask=np.full((6, 7), False), pixel_scale=2.0, sub_grid_size=1)

            assert (sub_mapper == sub_mapper_util).all()

            msk = mask.Mask(array=np.full((5, 4), False), pixel_scale=2.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=2,
                                                                                       psf_shape=(3, 3))

            sub_mapper_util = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(
                mask=np.full((7, 6), False), pixel_scale=2.0, sub_grid_size=2)

            assert (sub_mapper == sub_mapper_util).all()

            msk = mask.Mask(array=np.full((2, 5), False), pixel_scale=8.0)

            sub_mapper = grids.SubGridMapper.mapper_from_mask_sub_grid_size_and_psf_shape(mask=msk, sub_grid_size=4,
                                                                                       psf_shape=(5, 5))

            sub_mapper_util = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(
                mask=np.full((6, 9), False), pixel_scale=8.0, sub_grid_size=4)

            assert (sub_mapper == sub_mapper_util).all()


    class TestTrimPaddedArrayToOriginal:

        def test__map_padded_4x4__unmasked_1d_array_to_2d_array_and_trim_to_original_2x2(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(2, 2), padded_shape=(4 , 4))

            padded_array_2d = np.array([[1.0,  2.0,  3.0,  4.0],
                                        [5.0,  6.0,  7.0,  8.0],
                                        [9.0, 10.0, 11.0, 12.0],
                                        [13.0, 14.0, 15.0, 16.0]])
            array_2d = image_mapper.trim_padded_array_to_original_shape(padded_array_2d)

            assert (array_2d == np.array([[ 6.0,  7.0],
                                          [10.0, 11.0]])).all()

        def test__map_padded_5x3__unmasked_1d_array_to_2d_array_and_trim_to_original_3x1(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(3 , 1), padded_shape=(5 , 3))

            padded_array_2d = np.array([[1.0,  2.0,  3.0],
                                 [4.0,  5.0,  6.0],
                                 [7.0,  8.0,  9.0],
                                 [10.0, 11.0, 12.0],
                                 [13.0, 14.0, 15.0]])
            array_2d = image_mapper.trim_padded_array_to_original_shape(padded_array_2d)

            assert (array_2d == np.array([[5.0],
                                          [8.0],
                                          [11.0]])).all()

        def test__map_padded_3x5__unmasked_1d_array_to_2d_array_and_trim_to_original_1x3(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(1, 3), padded_shape=(3 , 5))

            padded_array_2d = np.array([[1.0,  2.0,  3.0, 4.0,  5.0],
                                 [6.0,  7.0,  8.0,  9.0, 10.0],
                                 [11.0, 12.0, 13.0, 14.0, 15.0]])
            array_2d = image_mapper.trim_padded_array_to_original_shape(padded_array_2d)

            assert (array_2d == np.array([[7.0, 8.0, 9.0]])).all()

        def test__map_padded_7x3__unmasked_1d_array_to_2d_array_and_trim_to_original_5x1(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(5 , 1), padded_shape=(7 , 3))

            padded_array_2d = np.array([[1.0,  2.0,  3.0],
                                 [4.0,  5.0,  6.0],
                                 [7.0,  8.0,  9.0],
                                 [10.0, 11.0, 12.0],
                                 [13.0, 14.0, 15.0],
                                 [16.0, 17.0, 18.0],
                                 [19.0, 20.0, 21.0]])

            array_2d = image_mapper.trim_padded_array_to_original_shape(padded_array_2d)

            assert (array_2d == np.array([[5.0],
                                          [8.0],
                                          [11.0],
                                          [14.0],
                                          [17.0]])).all()

        def test__map_padded_4x7__unmasked_1d_array_to_2d_array_and_trim_to_original_2x5(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(2 , 5), padded_shape=(4, 7))

            padded_array_2d = np.array([[1.0,  2.0,  3.0,  4.0,  5.0,  6.0,  7.0],
                                 [8.0,  9.0, 10.0, 11.0, 12.0, 13.0, 14.0],
                                 [15.0, 16.0, 17.0, 18.0, 19.0, 20.0, 21.0],
                                 [22.0, 23.0, 24.0, 25.0, 26.0, 27.0, 28.0]])

            array_2d = image_mapper.trim_padded_array_to_original_shape(padded_array_2d)

            assert (array_2d == np.array([[9.0,  10.0, 11.0, 12.0, 13.0],
                                          [16.0, 17.0, 18.0, 19.0, 20.0]])).all()


    class TestConvolveAndTrim:

        def test__convolve_1d_mapper_array_with_psf_and_trim_to_original_size(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(2 , 2), padded_shape=(4 , 4))

            array_1d = np.array([0.0, 0.0, 0.0, 0.0,
                                 0.0, 0.0, 0.0, 0.0,
                                 0.0, 1.0, 0.0, 0.0,
                                 0.0, 0.0, 0.0, 0.0])

            kernel = np.array([[0.0, 1.0, 0.0],
                               [1.0, 2.0, 1.0],
                               [0.0, 1.0, 0.0]])

            psf = image.PSF(array=kernel)

            blurred_array_1d = image_mapper.convolve_unmasked_array_with_psf_and_trim(array_1d, psf)

            assert (blurred_array_1d == np.array([1.0, 0.0,
                                                  2.0, 1.0])).all()

        def test__same_as_above_but_different_quantities(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(3 , 2), padded_shape=(5 , 4))

            array_1d = np.array([0.0, 0.0, 0.0, 0.0,
                                 0.0, 0.0, 0.0, 0.0,
                                 0.0, 1.0, 0.0, 0.0,
                                 0.0, 0.0, 0.0, 0.0,
                                 1.0, 0.0, 0.0, 0.0])

            kernel = np.array([[1.0, 1.0, 4.0],
                               [1.0, 3.0, 1.0],
                               [1.0, 1.0, 1.0]])

            psf = image.PSF(array=kernel)

            blurred_array_1d = image_mapper.convolve_unmasked_array_with_psf_and_trim(array_1d, psf)

            assert (blurred_array_1d == np.array([1.0, 4.0,
                                                  3.0, 1.0,
                                                  5.0, 1.0])).all()


    class TestMapUnmaskedArrays:

        def test__map_original_2x2_from_1d(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(2 , 2), padded_shape=(4 , 4))

            array_1d = np.array([6.0,  7.0,
                                 9.0, 10.0])
            array_2d = image_mapper.map_unmasked_1d_array_to_2d_array(array_1d)

            assert (array_2d == np.array([[6.0,  7.0],
                                          [9.0, 10.0]])).all()

        def test__map_original_3x1_from_1d(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(3 , 1), padded_shape=(5 , 3))

            array_1d = np.array([5.0,
                                 8.0,
                                11.0])
            array_2d = image_mapper.map_unmasked_1d_array_to_2d_array(array_1d)

            assert (array_2d == np.array([[5.0],
                                          [8.0],
                                          [11.0]])).all()

        def test__map_original_1x3__from_1d(self):

            image_mapper = grids.ImageGridMapper(arr=np.empty((0)), original_shape=(1, 3), padded_shape=(3 , 5))

            array_1d = np.array([7.0,  8.0,  9.0])
            array_2d = image_mapper.map_unmasked_1d_array_to_2d_array(array_1d)

            assert (array_2d == np.array([[7.0, 8.0, 9.0]])).all()


class TestGridCollection(object):

    def test__grids(self, lensing_grids):

        assert (lensing_grids.image == np.array([[0., 0.]])).all()
        np.testing.assert_almost_equal(lensing_grids.sub, np.array([[-0.16666667, -0.16666667],
                                                            [-0.16666667, 0.16666667],
                                                            [0.16666667, -0.16666667],
                                                            [0.16666667, 0.16666667]]))
        assert (lensing_grids.blurring == np.array([[-1., -1.],
                                            [-1., 0.],
                                            [-1., 1.],
                                            [0., -1.],
                                            [0., 1.],
                                            [1., -1.],
                                            [1., 0.],
                                            [1., 1.]])).all()

    def test__mapper_grids(self):

        msk = np.array([[False, False],
                        [False, False]])

        msk = mask.Mask(msk, pixel_scale=1.0)

        grid_mappers = grids.LensingGrids.grid_mappers_from_mask_sub_grid_size_and_psf_shape(msk, sub_grid_size=2,
                                                                                             psf_shape=(3,3))

        image_mapper_util = imaging_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((4, 4), False),
                                                                                     pixel_scale=1.0)

        sub_mapper_util = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask=np.full((4, 4), False),
                                                                                               pixel_scale=1.0, sub_grid_size=2)

        assert (grid_mappers.image == image_mapper_util).all()
        assert grid_mappers.image.original_shape == (2 ,2)
        assert grid_mappers.image.padded_shape == (4 ,4)

        assert (grid_mappers.sub == sub_mapper_util).all()
        assert grid_mappers.sub.original_shape == (2 ,2)
        assert grid_mappers.sub.padded_shape == (4 ,4)

        assert (grid_mappers.blurring == np.array([[0.0, 0.0]])).all()

    def test__for_simulation(self):

        grid_mappers = grids.LensingGrids.for_simulation(shape=(2, 2), pixel_scale=1.0, sub_grid_size=2,
                                                         psf_shape=(3,3))

        image_mapper_util = imaging_util.image_grid_masked_from_mask_and_pixel_scale(mask=np.full((4, 4), False),
                                                                                     pixel_scale=1.0)

        sub_mapper_util = imaging_util.sub_grid_masked_from_mask_pixel_scale_and_sub_grid_size(mask=np.full((4, 4), False),
                                                                                      pixel_scale=1.0, sub_grid_size=2)

        assert (grid_mappers.image == image_mapper_util).all()
        assert grid_mappers.image.original_shape == (2 ,2)
        assert grid_mappers.image.padded_shape == (4 ,4)

        assert (grid_mappers.sub == sub_mapper_util).all()
        assert grid_mappers.sub.original_shape == (2 ,2)
        assert grid_mappers.sub.padded_shape == (4 ,4)

        assert (grid_mappers.blurring == np.array([[0.0, 0.0]])).all()

    def test__apply_function(self, lensing_grids):
        def add_one(coords):
            return np.add(1, coords)

        new_collection = lensing_grids.apply_function(add_one)
        assert isinstance(new_collection, grids.LensingGrids)
        assert (new_collection.image == np.add(1, np.array([[0., 0.]]))).all()
        np.testing.assert_almost_equal(new_collection.sub, np.add(1, np.array([[-0.16666667, -0.16666667],
                                                                               [-0.16666667, 0.16666667],
                                                                               [0.16666667, -0.16666667],
                                                                               [0.16666667, 0.16666667]])))
        assert (new_collection.blurring == np.add(1, np.array([[-1., -1.],
                                                               [-1., 0.],
                                                               [-1., 1.],
                                                               [0., -1.],
                                                               [0., 1.],
                                                               [1., -1.],
                                                               [1., 0.],
                                                               [1., 1.]]))).all()

    def test__map_function(self, lensing_grids):
        def add_number(coords, number):
            return np.add(coords, number)

        new_collection = lensing_grids.map_function(add_number, [1, 2, 3])

        assert isinstance(new_collection, grids.LensingGrids)
        assert (new_collection.image == np.add(1, np.array([[0., 0.]]))).all()
        np.testing.assert_almost_equal(new_collection.sub, np.add(2, np.array([[-0.16666667, -0.16666667],
                                                                               [-0.16666667, 0.16666667],
                                                                               [0.16666667, -0.16666667],
                                                                               [0.16666667, 0.16666667]])))
        assert (new_collection.blurring == np.add(3, np.array([[-1., -1.],
                                                               [-1., 0.],
                                                               [-1., 1.],
                                                               [0., -1.],
                                                               [0., 1.],
                                                               [1., -1.],
                                                               [1., 0.],
                                                               [1., 1.]]))).all()


class TestBorderCollection(object):


    class TestSetup:

        def test__simple_setup_using_constructor(self):

            image_border = grids.ImageGridBorder(arr=np.array([1, 2, 5]), polynomial_degree=4, centre=(1.0, 1.0))
            sub_border = grids.SubGridBorder(arr=np.array([1, 2, 3]), polynomial_degree=2, centre=(0.0, 1.0))

            border_collection = grids.BorderCollection(image=image_border, sub=sub_border)

            assert (border_collection.image == np.array([1, 2, 5])).all()
            assert border_collection.image.polynomial_degree == 4
            assert border_collection.image.centre == (1.0, 1.0)

            assert (border_collection.sub == np.array([1, 2, 3])).all()
            assert border_collection.sub.polynomial_degree == 2
            assert border_collection.sub.centre == (0.0, 1.0)

        def test__setup_from_mask(self):

            msk = np.array([[True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, False, False, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True]])

            msk = mask.Mask(msk, pixel_scale=3.0)

            border_collection = grids.BorderCollection.from_mask_and_sub_grid_size(mask=msk, sub_grid_size=2)

            assert (border_collection.image == np.array([0, 1])).all()
            assert (border_collection.sub == np.array([0, 5])).all()


    class TestRelocatedGridsFromGrids:

        def test__simple_case__new_grids_have_relocates(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            image_grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            image_grid = image_grid_circle
            image_grid.append(np.array([0.1, 0.0]))
            image_grid.append(np.array([-0.2, -0.3]))
            image_grid.append(np.array([0.5, 0.4]))
            image_grid.append(np.array([0.7, -0.1]))
            image_grid = np.asarray(image_grid)

            from autolens.lensing import grids

            image_border = grids.ImageGridBorder(arr=np.arange(32), polynomial_degree=3)

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            sub_grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            sub_grid = sub_grid_circle
            sub_grid.append(np.array([2.5, 0.0]))
            sub_grid.append(np.array([0.0, 3.0]))
            sub_grid.append(np.array([-2.5, 0.0]))
            sub_grid.append(np.array([-5.0, 5.0]))
            sub_grid = np.asarray(sub_grid)

            sub_border = grids.SubGridBorder(arr=np.arange(32), polynomial_degree=3)

            borders = grids.BorderCollection(image=image_border, sub=sub_border)

            grids = grids.LensingGrids(image=image_grid, sub=sub_grid, blurring=None)

            relocated_grids = borders.relocated_grids_from_grids(grids)

            assert relocated_grids.image[0:32] == pytest.approx(np.asarray(image_grid_circle)[0:32], 1e-3)
            assert relocated_grids.image[32] == pytest.approx(np.array([0.1, 0.0]), 1e-3)
            assert relocated_grids.image[33] == pytest.approx(np.array([-0.2, -0.3]), 1e-3)
            assert relocated_grids.image[34] == pytest.approx(np.array([0.5, 0.4]), 1e-3)
            assert relocated_grids.image[35] == pytest.approx(np.array([0.7, -0.1]), 1e-3)

            assert relocated_grids.sub[0:32] == pytest.approx(np.asarray(sub_grid_circle)[0:32], 1e-3)
            assert relocated_grids.sub[32] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert relocated_grids.sub[33] == pytest.approx(np.array([0.0, 1.0]), 1e-3)
            assert relocated_grids.sub[34] == pytest.approx(np.array([-1.0, 0.0]), 1e-3)
            assert relocated_grids.sub[35] == pytest.approx(np.array([-0.707, 0.707]), 1e-3)


class TestIGridBorder(object):


    class TestFromMask:

        def test__simple_mask_border_pixel_is_pixel(self):

            msk = np.array([[True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, False, False, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True]])

            msk = mask.Mask(msk, pixel_scale=3.0)

            border = grids.ImageGridBorder.from_mask(msk)

            assert (border == np.array([0, 1])).all()


    class TestThetasAndRadii:

        def test__four_grid_in_circle__all_in_border__correct_radii_and_thetas(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            radii = border.grid_to_radii(grid)
            thetas = border.grid_to_thetas(grid)

            assert (radii == np.array([1.0, 1.0, 1.0, 1.0])).all()
            assert (thetas == np.array([0.0, 90.0, 180.0, 270.0])).all()

        def test__other_thetas_radii(self):
            grid = np.array([[2.0, 0.0], [2.0, 2.0], [-1.0, -1.0], [0.0, -3.0]])

            border = grids.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            radii = border.grid_to_radii(grid)
            thetas = border.grid_to_thetas(grid)

            assert (radii == np.array([2.0, 2.0 * np.sqrt(2), np.sqrt(2.0), 3.0])).all()
            assert (thetas == np.array([0.0, 45.0, 225.0, 270.0])).all()

        def test__border_centre_offset__grid_same_r_and_theta_shifted(self):

            grid = np.array([[2.0, 1.0], [1.0, 2.0], [0.0, 1.0], [1.0, 0.0]])

            border = grids.ImageGridBorder(arr=np.arange(4), polynomial_degree=3, centre=(1.0, 1.0))
            radii = border.grid_to_radii(grid)
            thetas = border.grid_to_thetas(grid)

            assert (radii == np.array([1.0, 1.0, 1.0, 1.0])).all()
            assert (thetas == np.array([0.0, 90.0, 180.0, 270.0])).all()


    class TestBorderPolynomialFit(object):

        def test__four_grid_in_circle__thetas_at_radius_are_each_grid_radius(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            poly = border.polynomial_fit_to_border(grid)

            assert np.polyval(poly, 0.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 90.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 180.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 270.0) == pytest.approx(1.0, 1e-3)

        def test__eight_grid_in_circle__thetas_at_each_grid_are_the_radius(self):

            grid = np.array([[1.0, 0.0], [0.5 * np.sqrt(2), 0.5 * np.sqrt(2)],
                             [0.0, 1.0], [-0.5 * np.sqrt(2), 0.5 * np.sqrt(2)],
                             [-1.0, 0.0], [-0.5 * np.sqrt(2), -0.5 * np.sqrt(2)],
                             [0.0, -1.0], [0.5 * np.sqrt(2), -0.5 * np.sqrt(2)]])

            border = grids.ImageGridBorder(arr=
                                          np.arange(8), polynomial_degree=3)
            poly = border.polynomial_fit_to_border(grid)

            assert np.polyval(poly, 0.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 45.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 90.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 135.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 180.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 225.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 270.0) == pytest.approx(1.0, 1e-3)
            assert np.polyval(poly, 315.0) == pytest.approx(1.0, 1e-3)


    class TestMoveFactors(object):

        def test__inside_border__move_factor_is_1(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0]])

            border = grids.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            move_factors = border.move_factors_from_grid(grid)

            assert move_factors[0] == pytest.approx(1.0, 1e-4)
            assert move_factors[1] == pytest.approx(1.0, 1e-4)
            assert move_factors[2] == pytest.approx(1.0, 1e-4)
            assert move_factors[3] == pytest.approx(1.0, 1e-4)

        def test__outside_border_double_its_radius__move_factor_is_05(self):

            grid = np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0],
                             [2.0, 0.0], [0.0, 2.0], [-2.0, 0.0], [0.0, -2.0]])

            border = grids.ImageGridBorder(arr=np.arange(4), polynomial_degree=3)
            move_factors = border.move_factors_from_grid(grid)

            assert move_factors[0] == pytest.approx(1.0, 1e-4)
            assert move_factors[1] == pytest.approx(1.0, 1e-4)
            assert move_factors[2] == pytest.approx(1.0, 1e-4)
            assert move_factors[3] == pytest.approx(1.0, 1e-4)
            assert move_factors[4] == pytest.approx(0.5, 1e-4)
            assert move_factors[5] == pytest.approx(0.5, 1e-4)
            assert move_factors[6] == pytest.approx(0.5, 1e-4)
            assert move_factors[7] == pytest.approx(0.5, 1e-4)

        def test__outside_border_as_above__but_shift_for_source_plane_centre(self):

            grid = np.array([[2.0, 1.0], [1.0, 2.0], [0.0, 1.0], [1.0, 0.0],
                             [3.0, 1.0], [1.0, 3.0], [1.0, 3.0], [3.0, 1.0]])

            border = grids.ImageGridBorder(arr=np.arange(4), polynomial_degree=3, centre=(1.0, 1.0))
            move_factors = border.move_factors_from_grid(grid)

            assert move_factors[0] == pytest.approx(1.0, 1e-4)
            assert move_factors[1] == pytest.approx(1.0, 1e-4)
            assert move_factors[2] == pytest.approx(1.0, 1e-4)
            assert move_factors[3] == pytest.approx(1.0, 1e-4)
            assert move_factors[4] == pytest.approx(0.5, 1e-4)
            assert move_factors[5] == pytest.approx(0.5, 1e-4)
            assert move_factors[6] == pytest.approx(0.5, 1e-4)
            assert move_factors[7] == pytest.approx(0.5, 1e-4)


    class TestRelocateCoordinates(object):

        def test__inside_border_no_relocations(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            grid = grid_circle
            grid.append(np.array([0.1, 0.0]))
            grid.append(np.array([-0.2, -0.3]))
            grid.append(np.array([0.5, 0.4]))
            grid.append(np.array([0.7, -0.1]))
            grid = np.asarray(grid)

            border = grids.ImageGridBorder(arr=np.arange(32), polynomial_degree=3)
            relocated_grid = border.relocated_grid_from_grid(grid)

            assert relocated_grid[0:32] == pytest.approx(np.asarray(grid_circle)[0:32], 1e-3)
            assert relocated_grid[32] == pytest.approx(np.array([0.1, 0.0]), 1e-3)
            assert relocated_grid[33] == pytest.approx(np.array([-0.2, -0.3]), 1e-3)
            assert relocated_grid[34] == pytest.approx(np.array([0.5, 0.4]), 1e-3)
            assert relocated_grid[35] == pytest.approx(np.array([0.7, -0.1]), 1e-3)

        def test__outside_border_simple_cases__relocates_to_source_border(self):

            thetas = np.linspace(0.0, 2.0 * np.pi, 32)
            grid_circle = list(map(lambda x: (np.cos(x), np.sin(x)), thetas))
            grid = grid_circle
            grid.append(np.array([2.5, 0.0]))
            grid.append(np.array([0.0, 3.0]))
            grid.append(np.array([-2.5, 0.0]))
            grid.append(np.array([-5.0, 5.0]))
            grid = np.asarray(grid)

            border = grids.ImageGridBorder(arr=np.arange(32), polynomial_degree=3)
            relocated_grid = border.relocated_grid_from_grid(grid)

            assert relocated_grid[0:32] == pytest.approx(np.asarray(grid_circle)[0:32], 1e-3)
            assert relocated_grid[32] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert relocated_grid[33] == pytest.approx(np.array([0.0, 1.0]), 1e-3)
            assert relocated_grid[34] == pytest.approx(np.array([-1.0, 0.0]), 1e-3)
            assert relocated_grid[35] == pytest.approx(np.array([-0.707, 0.707]), 1e-3)

        def test__6_grid_total__2_outside_border__different_border__relocate_to_source_border(self):

            grid = np.array([[1.0, 0.0], [20., 20.], [0.0, 1.0], [-1.0, 0.0], [0.0, -1.0], [1.0, 1.0]])
            border_pixels = np.array([0, 2, 3, 4])

            border = grids.ImageGridBorder(border_pixels, polynomial_degree=3)

            relocated_grid = border.relocated_grid_from_grid(grid)

            assert relocated_grid[0] == pytest.approx(grid[0], 1e-3)
            assert relocated_grid[1] == pytest.approx(np.array([0.7071, 0.7071]), 1e-3)
            assert relocated_grid[2] == pytest.approx(grid[2], 1e-3)
            assert relocated_grid[3] == pytest.approx(grid[3], 1e-3)
            assert relocated_grid[4] == pytest.approx(grid[4], 1e-3)
            assert relocated_grid[5] == pytest.approx(np.array([0.7071, 0.7071]), 1e-3)


    class TestSubGridBorder(object):

        def test__simple_mask_border_pixel_is_pixel(self):

            msk = np.array([[True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, False, False, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True],
                            [True, True, True, True, True, True, True]])

            msk = mask.Mask(msk, pixel_scale=3.0)

            border = grids.SubGridBorder.from_mask(msk, sub_grid_size=2)

            assert (border == np.array([0, 5])).all()
