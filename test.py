import  torch
import torch.nn as nn
import torch.nn.functional as F

import argparse
import os
import time
from dataset import CPDataset, CPDataLoader
from network import GMM, UnetGenerator, load_checkpoint
from PIL import Image
import shutil


def save_images(img_tensors, img_names, save_dir):
    for img_tensor, img_name in zip(img_tensors, img_names):
        tensor = (img_tensor.clone()+1)*0.5 * 255
        tensor = tensor.cpu().clamp(0, 255)

        array = tensor.numpy().astype('uint8')
        if array.shape[0] == 1:
            array = array.squeeze(0)
        elif array.shape[0] == 3:
            array = array.swapaxes(0, 1).swapaxes(1, 2)

        Image.fromarray(array).save(os.path.join(save_dir, img_name))

def get_opt1():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f')
    parser.add_argument("--name", default="GMM")
    # parser.add_argument("--name", default="TOM")

    parser.add_argument("--gpu_ids", default="")
    parser.add_argument('-j', '--workers', type=int, default=0)
    parser.add_argument('-b', '--batch-size', type=int, default=1)

    parser.add_argument("--dataroot", default="D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data")

    parser.add_argument("--datamode", default="train")
    # parser.add_argument("--datamode", default="test")

    parser.add_argument("--stage", default="GMM")
    # parser.add_argument("--stage", default="TOM")

    parser.add_argument("--data_list", default="train/train_pairs.txt")
    # parser.add_argument("--data_list", default="test_pairs.txt")
    # parser.add_argument("--data_list", default="test_pairs_same.txt")

    parser.add_argument("--fine_width", type=int, default=192)
    parser.add_argument("--fine_height", type=int, default=256)
    parser.add_argument("--radius", type=int, default=5)
    parser.add_argument("--grid_size", type=int, default=5)

    parser.add_argument('--tensorboard_dir', type=str,
                        default='tensorboard', help='save tensorboard infos')

    parser.add_argument('--result_dir', type=str,
                        default='D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data', help='save result infos')

    parser.add_argument('--checkpoint', type=str, default='D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/models/gmm_final.pth', help='model checkpoint for test')
    # parser.add_argument('--checkpoint', type=str, default='checkpoints/TOM/tom_final.pth', help='model checkpoint for test')

    parser.add_argument("--display_count", type=int, default=1)
    parser.add_argument("--shuffle", action='store_true',
                        help='shuffle input data')

    opt = parser.parse_args()
    return opt

def get_opt2():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f')
    # parser.add_argument("--name", default="GMM")
    parser.add_argument("--name", default="TOM")

    parser.add_argument("--gpu_ids", default="")
    parser.add_argument('-j', '--workers', type=int, default=0)
    parser.add_argument('-b', '--batch-size', type=int, default=1)

    parser.add_argument("--dataroot", default="D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data")

    parser.add_argument("--datamode", default="train")
    # parser.add_argument("--datamode", default="test")

    # parser.add_argument("--stage", default="GMM")
    parser.add_argument("--stage", default="TOM")

    parser.add_argument("--data_list", default="train/train_pairs.txt")
    # parser.add_argument("--data_list", default="test_pairs.txt")
    # parser.add_argument("--data_list", default="test_pairs_same.txt")

    parser.add_argument("--fine_width", type=int, default=192)
    parser.add_argument("--fine_height", type=int, default=256)
    parser.add_argument("--radius", type=int, default=5)
    parser.add_argument("--grid_size", type=int, default=5)

    parser.add_argument('--tensorboard_dir', type=str,
                        default='tensorboard', help='save tensorboard infos')

    parser.add_argument('--result_dir', type=str,
                        default='D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data', help='save result infos')

    parser.add_argument('--checkpoint', type=str, default='D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/models/tom_final.pth', help='model checkpoint for test')
    # parser.add_argument('--checkpoint', type=str, default='checkpoints/TOM/tom_final.pth', help='model checkpoint for test')

    parser.add_argument("--display_count", type=int, default=1)
    parser.add_argument("--shuffle", action='store_true',
                        help='shuffle input data')

    opt = parser.parse_args()
    return opt

def test_gmm(opt, test_loader, model):
    # model.cuda()
    model.eval()

    base_name = os.path.basename(opt.checkpoint)
    name = opt.name
    save_dir = os.path.join(opt.result_dir, name, opt.datamode)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    warp_cloth_dir = os.path.join(save_dir, 'warp-cloth')
    if not os.path.exists(warp_cloth_dir):
        os.makedirs(warp_cloth_dir)
    warp_mask_dir = os.path.join(save_dir, 'warp-mask')
    if not os.path.exists(warp_mask_dir):
        os.makedirs(warp_mask_dir)
    result_dir1 = os.path.join(save_dir, 'result_dir')
    if not os.path.exists(result_dir1):
        os.makedirs(result_dir1)
    overlayed_TPS_dir = os.path.join(save_dir, 'overlayed_TPS')
    if not os.path.exists(overlayed_TPS_dir):
        os.makedirs(overlayed_TPS_dir)
    warped_grid_dir = os.path.join(save_dir, 'warped_grid')
    if not os.path.exists(warped_grid_dir):
        os.makedirs(warped_grid_dir)
    for step, inputs in enumerate(test_loader.data_loader):
        iter_start_time = time.time()

        c_names = inputs['c_name']
        im_names = inputs['im_name']
        im = inputs['image']
        im_pose = inputs['pose_image']
        im_h = inputs['head']
        shape = inputs['shape']
        agnostic = inputs['agnostic']
        c = inputs['cloth']
        cm = inputs['cloth_mask']
        im_c = inputs['parse_cloth']
        im_g = inputs['grid_image']
        shape_ori = inputs['shape_ori']  # original body shape without blurring

        grid, theta = model(agnostic, cm)
        warped_cloth = F.grid_sample(c, grid, padding_mode='border', align_corners=True)
        warped_mask = F.grid_sample(cm, grid, padding_mode='zeros', align_corners=True)
        warped_grid = F.grid_sample(im_g, grid, padding_mode='zeros', align_corners=True)
        overlay = 0.7 * warped_cloth + 0.3 * im

        visuals = [[im_h, shape, im_pose],
                   [c, warped_cloth, im_c],
                   [warped_grid, (warped_cloth+im)*0.5, im]]

        # save_images(warped_cloth, c_names, warp_cloth_dir)
        # save_images(warped_mask*2-1, c_names, warp_mask_dir)
        save_images(warped_cloth, im_names, warp_cloth_dir)
        save_images(warped_mask * 2 - 1, im_names, warp_mask_dir)
        save_images(shape_ori * 0.2 + warped_cloth *
                    0.8, im_names, result_dir1)
        save_images(warped_grid, im_names, warped_grid_dir)
        save_images(overlay, im_names, overlayed_TPS_dir)

        if (step+1) % opt.display_count == 0:
            # board_add_images(board, 'combine', visuals, step+1)
            t = time.time() - iter_start_time
            print('step: %8d, time: %.3f' % (step+1, t), flush=True)

def test_tom(opt, test_loader, model):
    
    model.eval()

    base_name = os.path.basename(opt.checkpoint)
    # save_dir = os.path.join(opt.result_dir, base_name, opt.datamode)
    save_dir = os.path.join(opt.result_dir, opt.name, opt.datamode)
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    try_on_dir = os.path.join(save_dir, 'try-on')
    if not os.path.exists(try_on_dir):
        os.makedirs(try_on_dir)
    p_rendered_dir = os.path.join(save_dir, 'p_rendered')
    if not os.path.exists(p_rendered_dir):
        os.makedirs(p_rendered_dir)
    m_composite_dir = os.path.join(save_dir, 'm_composite')
    if not os.path.exists(m_composite_dir):
        os.makedirs(m_composite_dir)
    im_pose_dir = os.path.join(save_dir, 'im_pose')
    if not os.path.exists(im_pose_dir):
        os.makedirs(im_pose_dir)
    shape_dir = os.path.join(save_dir, 'shape')
    if not os.path.exists(shape_dir):
        os.makedirs(shape_dir)
    im_h_dir = os.path.join(save_dir, 'im_h')
    if not os.path.exists(im_h_dir):
        os.makedirs(im_h_dir)  # for test data

    print('Dataset size: %05d!' % (len(test_loader.dataset)), flush=True)
    for step, inputs in enumerate(test_loader.data_loader):
        iter_start_time = time.time()

        im_names = inputs['im_name']
        im = inputs['image']
        im_pose = inputs['pose_image']
        im_h = inputs['head']
        shape = inputs['shape']

        agnostic = inputs['agnostic']
        c = inputs['cloth']
        cm = inputs['cloth_mask']

        # outputs = model(torch.cat([agnostic, c], 1))  # CP-VTON
        outputs = model(torch.cat([agnostic, c, cm], 1))  # CP-VTON+
        p_rendered, m_composite = torch.split(outputs, 3, 1)
        p_rendered = F.tanh(p_rendered)
        m_composite = F.sigmoid(m_composite)
        p_tryon = c * m_composite + p_rendered * (1 - m_composite)

        visuals = [[im_h, shape, im_pose],
                   [c, 2*cm-1, m_composite],
                   [p_rendered, p_tryon, im]]

        save_images(p_tryon, im_names, try_on_dir)
        save_images(im_h, im_names, im_h_dir)
        save_images(shape, im_names, shape_dir)
        save_images(im_pose, im_names, im_pose_dir)
        save_images(m_composite, im_names, m_composite_dir)
        save_images(p_rendered, im_names, p_rendered_dir)  # For test data

        if (step+1) % opt.display_count == 0:
            # board_add_images(board, 'combine', visuals, step+1)
            t = time.time() - iter_start_time
            print('step: %8d, time: %.3f' % (step+1, t), flush=True)

def test1():
    opt = get_opt1()
    print(opt)
    print("Start to test stage: %s, named: %s!" % (opt.stage, opt.name))

    # create dataset
    test_dataset = CPDataset(opt)

    # create dataloader
    test_loader = CPDataLoader(opt, test_dataset)

    # # visualization
    # if not os.path.exists(opt.tensorboard_dir):
    #     os.makedirs(opt.tensorboard_dir)
    # board = SummaryWriter(logdir=os.path.join(opt.tensorboard_dir, opt.name))

    # create model & test
    if opt.stage == 'GMM':
        model = GMM(opt)
        load_checkpoint(model, opt.checkpoint)
        with torch.no_grad():
            test_gmm(opt, test_loader, model)
    elif opt.stage == 'TOM':
        # model = UnetGenerator(25, 4, 6, ngf=64, norm_layer=nn.InstanceNorm2d)  # CP-VTON
        model = UnetGenerator(26, 4, 6, ngf=64, norm_layer=nn.InstanceNorm2d)  # CP-VTON+
        load_checkpoint(model, opt.checkpoint)
        with torch.no_grad():
            test_tom(opt, test_loader, model)
    else:
        raise NotImplementedError('Model [%s] is not implemented' % opt.stage)

    print('Finished test %s, named: %s!' % (opt.stage, opt.name))
def test2():
    opt = get_opt2()
    print(opt)
    print("Start to test stage: %s, named: %s!" % (opt.stage, opt.name))

    # create dataset
    test_dataset = CPDataset(opt)

    # create dataloader
    test_loader = CPDataLoader(opt, test_dataset)

    # # visualization
    # if not os.path.exists(opt.tensorboard_dir):
    #     os.makedirs(opt.tensorboard_dir)
    # board = SummaryWriter(logdir=os.path.join(opt.tensorboard_dir, opt.name))

    # create model & test
    if opt.stage == 'GMM':
        model = GMM(opt)
        load_checkpoint(model, opt.checkpoint)
        with torch.no_grad():
            test_gmm(opt, test_loader, model)
    elif opt.stage == 'TOM':
        # model = UnetGenerator(25, 4, 6, ngf=64, norm_layer=nn.InstanceNorm2d)  # CP-VTON
        model = UnetGenerator(26, 4, 6, ngf=64, norm_layer=nn.InstanceNorm2d)  # CP-VTON+
        load_checkpoint(model, opt.checkpoint)
        with torch.no_grad():
            test_tom(opt, test_loader, model)
    else:
        raise NotImplementedError('Model [%s] is not implemented' % opt.stage)

    print('Finished test %s, named: %s!' % (opt.stage, opt.name))
def remo():
    shutil.rmtree('D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/warp-cloth')
    shutil.rmtree('D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/warp-mask')

def transf():
    shutil.copytree('D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/GMM/train/warp-cloth', 'D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/warp-cloth')
    shutil.copytree('D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/GMM/train/warp-mask', 'D:/IIT Jodhpr/3rd year/2nd sem/deep learning/DL_ops project/Deploy/data/train/warp-mask')

test1()
remo()
transf()
test2()