#%%
import itk
from itkwidgets import compare, checkerboard, view

# Import Images
fixed_image = itk.imread("E:\\Parotid\\nii_anon\\MR_021_anon\\T1_ax.nii", itk.F)
moving_image = itk.imread("E:\\Parotid\\nii_anon\\MR_021_anon\\T2_ax.nii", itk.F)

parameter_object = itk.ParameterObject.New()
default_rigid_parameter_map = parameter_object.GetDefaultParameterMap('rigid')
parameter_object.AddParameterMap(default_rigid_parameter_map)

# %%
# Call registration function
# result_image, result_transform_parameters = itk.elastix_registration_method(
#     fixed_image, moving_image,
#     parameter_object=parameter_object,)

# Load Elastix Image Filter Object
elastix_object = itk.ElastixRegistrationMethod.New(fixed_image, moving_image)
# elastix_object.SetFixedImage(fixed_image)
# elastix_object.SetMovingImage(moving_image)
elastix_object.SetParameterObject(parameter_object)

# Set additional options
elastix_object.SetLogToConsole(False)

# Update filter object (required)
elastix_object.UpdateLargestPossibleRegion()

# Results of Registration
result_image = elastix_object.GetOutput()
result_transform_parameters = elastix_object.GetTransformParameterObject()

itk.transformwrite(
    [result_transform_parameters],
    "/test.h5",
    compression=True,
)
# %%
