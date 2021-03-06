#import os
#os.environ['CUDA_VISIBLE_DEVICES'] = "0"
import tensorflow as tf
import numpy as np
import scipy.misc
import FID
import data_container as dc
from glob import glob
import os


#
# Functions taken from: https://github.com/carpedm20/DCGAN-tensorflow/blob/master/utils.py
#
def get_image(image_path, input_height, input_width,
              resize_height=64, resize_width=64,
              is_crop=True, is_grayscale=False):
  image = imread(image_path, is_grayscale)
  return transform(image, input_height, input_width,
                   resize_height, resize_width, is_crop)

def imread(path, is_grayscale = False):
  if (is_grayscale):
    return scipy.misc.imread(path, flatten = True).astype(np.float)
  else:
    return scipy.misc.imread(path).astype(np.float)

def transform(image, input_height, input_width,
              resize_height=64, resize_width=64, is_crop=True):
  if is_crop:
    cropped_image = center_crop(
      image, input_height, input_width,
      resize_height, resize_width)
  else:
    if (input_height != resize_height) or (input_width != resize_width):
      cropped_image = scipy.misc.imresize(image, [resize_height, resize_width])
    else:
      cropped_image = image
  return np.array(cropped_image) / 127.5 - 1.
#-------------------------------------------------------------------------------





# read N_IMGS data samples and store them in an data container
print("Reading data...", end="", flush=True)
celeb_path = "/publicdata/image/celebA_cropped/"# add path to celabA dataset
data = glob( os.path.join(celeb_path,"*"))
N_IMGS = 5000; N_FEATURES = 64*64*3
X = dc.DataContainer(np.zeros((N_IMGS, N_FEATURES)), epoch_shuffle=True)
for i in range(N_IMGS):
    img = get_image( data[i],
                    input_height=64,
                    input_width=64,
                    resize_height=64,
                    resize_width=64,
                    is_crop=False,
                    is_grayscale=False)
    X._data[i,:] = img.flatten()
X.minmax_scale_data(fac=256)
print("done")



# load inference model
# download model at: https://github.com/taey16/tf/blob/master/imagenet/classify_image_graph_def.pb
inc_pth = # add path to classify_image_graph_def.pb
FID.create_incpetion_graph(inc_pth)

# load precalculated statistics
stat_path = "."# add path to stat_trn.pkl.gz
sigma_trn, mu_trn = FID.load_stats("/system/user/mheusel/wrk/DCGAN/eval_imagenet/stat_trn.pkl.gz")


# get jpeg encoder
jpeg_tuple = FID.get_jpeg_encoder_tuple()

alphas = [ 0.75, 0.5, 0.25, 0.0]
init = tf.global_variables_initializer()
sess = tf.Session()
with sess.as_default():
    sess.run(init)
    query_tensor = FID.get_Fid_query_tensor(sess)
    for i,a in enumerate(alphas):
        X.apply_gauss_noise(alpha=a,scale=256)
        fid = FID.FID_unbatched( X.get_next_transformed_batch(N_IMGS)[0].reshape(-1,64,64,3),
                                 query_tensor,
                                 mu_trn,
                                 sigma_trn,
                                 jpeg_tuple,
                                 sess)
        print("-- alpha: " + str(a) + ", FID: " + str(fid))
