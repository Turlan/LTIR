import numpy as np
import argparse
import json
from PIL import Image
from os.path import join


def fast_hist(a, b, n):
    k = (a >= 0) & (a < n)
    return np.bincount(n * a[k].astype(int) + b[k], minlength=n ** 2).reshape(n, n)


def per_class_iu(hist):
    return np.diag(hist) / (hist.sum(1) + hist.sum(0) - np.diag(hist))


def label_mapping(input, mapping):
    output = np.copy(input)
    for ind in range(len(mapping)):
        output[input == mapping[ind][0]] = mapping[ind][1]
    return np.array(output, dtype=np.int64)


def compute_mIoU(pred_dir, i_iter):

    parser = argparse.ArgumentParser()
    parser.add_argument('--gt_dir', type=str, default='/media/cvpr-au/4TB_2/data/Cityscapes/gtFine/val', help='directory which stores CityScapes val gt images')
    parser.add_argument('--devkit_dir', default='dataset/cityscapes_list', help='base directory of cityscapes')
    args = parser.parse_args()

    gt_dir = args.gt_dir
    devkit_dir = args.devkit_dir

    with open(join(devkit_dir, 'info.json'), 'r') as fp:
      info = json.load(fp)
    num_classes = np.int(info['classes'])
    print('Num classes', num_classes)
    name_classes = np.array(info['label'], dtype=np.str)
    mapping = np.array(info['label2train'], dtype=np.int)
    hist = np.zeros((num_classes, num_classes))

    image_path_list = join(devkit_dir, 'val.txt')
    label_path_list = join(devkit_dir, 'label.txt')
    gt_imgs = open(label_path_list, 'r').read().splitlines()
    gt_imgs = [join(gt_dir, x) for x in gt_imgs]
    pred_imgs = open(image_path_list, 'r').read().splitlines()
    pred_imgs = [join(pred_dir, x.split('/')[-1]) for x in pred_imgs]

    for ind in range(len(gt_imgs)):
        pred = np.array(Image.open(pred_imgs[ind]))
        label = np.array(Image.open(gt_imgs[ind]))
        label = label_mapping(label, mapping)
        if len(label.flatten()) != len(pred.flatten()):
            print('Skipping: len(gt) = {:d}, len(pred) = {:d}, {:s}, {:s}'.format(len(label.flatten()), len(pred.flatten()), gt_imgs[ind], pred_imgs[ind]))
            continue
        hist += fast_hist(label.flatten(), pred.flatten(), num_classes)
        if ind > 0 and ind % 10 == 0:
            print('{:d} / {:d}: {:0.2f}'.format(ind, len(gt_imgs), 100*np.mean(per_class_iu(hist))))
        if i_iter == 0:
            break


    mIoUs = per_class_iu(hist)
    for ind_class in range(num_classes):
        mIoUs[ind_class] = round(mIoUs[ind_class] * 100, 1)

    for ind_class in range(num_classes):
        print('===>' + name_classes[ind_class] + ':\t' + str(mIoUs[ind_class]))

    iou19 = str(round(np.nanmean(mIoUs), 1))
    iou13 = str(round(np.mean(mIoUs[[0, 1, 2, 6, 7, 8, 10, 11, 12, 13, 15, 17, 18]]), 1))

    print('===> mIoU19: ' + iou19)
    print('===> mIoU13: ' + iou13)

    return iou19, iou13, str(mIoUs)

