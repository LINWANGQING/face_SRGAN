#!/usr/bin/env python

import argparse
import sys
import os
import  math
import torch
import torch.nn as nn
from torch.autograd import Variable
import  torch.nn as nn
import torchvision
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from torchvision.utils import save_image
from os import listdir,makedirs
from PIL import Image
import math
from   model.Model_Hourglass import *
from   model.GAN import *
from torch.utils.data.dataset import Dataset
from os.path import join
parser = argparse.ArgumentParser()
parser.add_argument('--dataset', type=str, default='folder', help='cifar10 | cifar100 | folder')
parser.add_argument('--dataroot', type=str, default='/media/ll/ll/lwq/lfw_mtcnnpy_160/Oswaldo_Paya', help='path to dataset')
parser.add_argument('--workers', type=int, default=1, help='number of data loading workers')
parser.add_argument('--batchSize', type=int, default=1, help='input batch size')
parser.add_argument('--imageSize', type=int, default=20, help='the low resolution image size')
parser.add_argument('--upSampling', type=int, default=6, help='low to high resolution scaling factor')
parser.add_argument('--cuda', default=True, help='enables cuda')
parser.add_argument('--nGPU', type=int, default=1, help='number of GPUs to use')
parser.add_argument('--generatorWeights', type=str, default='/home/ll/lwq/Pytorch-face/checkpoint/check2/Generator_model40.pth', help="path to generator weights (to continue training)")
parser.add_argument('--discriminatorWeights', type=str, default='/home/ll/lwq/Pytorch-face/checkpoint/check2/Discriminator_model40.pth', help="path to discriminator weights (to continue training)")

opt = parser.parse_args()
print(opt)

# try:
#     os.makedirs('/media/ll/ll/lwq/output/high_res_fake')
#     os.makedirs('/media/ll/ll/lwq/output/high_res_real')
#     os.makedirs('/media/ll/ll/lwq/output/low_res')
# except OSError:
#     pass


##############################
# class data_change(object): 
#     def __init__(self, rootfile):
#         super(data_change, self).__init__()
#         self.image_folder=listdir(rootfile) 
#         self.image_filenames=[]
#         for  folder in self.image_folder:
#             for filename in listdir(rootfile+'/'+folder):
#                 self.image_filenames.append(rootfile + "/" +folder+"/"+filename)
#                 # print("-*******",str(self.image_filenames[0]).split("/")[0])
#         self.transform=image_transforms()
#         # ipdb.set_trace()
#     def __getitem__(self,index):
#         hr_image=self.transform(Image.open(self.image_filenames[index]))
        
        
#         return  hr_image,self.image_filenames
#     def __len__(self):
#         return len(self.image_filenames)
# def image_transforms():
#     return transforms.Compose([
#         transforms.Resize(160),
#         transforms.ToTensor()
#         ])





if __name__ == '__main__':
    ##############################

    if torch.cuda.is_available() and not opt.cuda:
        print("WARNING: You have a CUDA device, so you should probably run with --cuda")

    # transform = transforms.Compose([transforms.Resize(opt.imageSize*opt.upSampling),
    #                                 transforms.ToTensor()])



    # scale = transforms.Compose([transforms.ToPILImage(),
    #                             # transforms.Resize(7,Image.BICUBIC),
    #                             transforms.Resize(20),
    #                             transforms.ToTensor(),
    #                             ])

 

    # if opt.dataset == 'folder':
    #     # folder dataset
    #     dataset=data_change(rootfile=opt.dataroot)
    #     # dataset = datasets.ImageFolder(root=opt.dataroot, transform=transform)
       

    # assert dataset

    # dataloader = torch.utils.data.DataLoader(dataset, batch_size=opt.batchSize,
    #                                          shuffle=False, num_workers=int(opt.workers))

    generator=Generator(128,opt.upSampling).eval()
    discriminator=Discriminator()
    faceAligNet=KFSGNet()
    

    generator.load_state_dict(torch.load('/home/ll/lwq/Pytorch-face/checkpoint/Generator_model40.pth'))
    generator = generator.train(False)
    discriminator.load_state_dict(torch.load('/home/ll/lwq/Pytorch-face/checkpoint/Discriminator_model20.pth'))
    faceAligNet.load_state_dict(torch.load('/home/ll/lwq/Pytorch-face/checkpoint/faceAligNet_model20.pth'))

    


    # For the content loss
    feature_extractor = FeatureExtractor(torchvision.models.vgg19(pretrained=True))
    print (feature_extractor)
    content_criterion = nn.MSELoss()
    adversarial_criterion = nn.BCELoss()

    target_real = Variable(torch.ones(opt.batchSize,1))
    target_fake = Variable(torch.zeros(opt.batchSize,1))

    # if gpu is to be used
    if opt.cuda:
        generator.cuda()
        discriminator.cuda()
        feature_extractor.cuda()
        content_criterion.cuda()
        adversarial_criterion.cuda()
        target_real = target_real.cuda()
        target_fake = target_fake.cuda()

    low_res = torch.FloatTensor(opt.batchSize, 3, opt.imageSize, opt.imageSize)

    print ('Test started...')
    ####################
    class TrainDatasetFromFolder(Dataset):
        def __init__(self, root):
            super(TrainDatasetFromFolder, self).__init__()
            self.image_filenames=[join(root, x) for x in listdir(root) ]
            self.hr_transforms = hr_transforms()
            
            

        def __getitem__(self, index):
            hr_image = self.hr_transforms(Image.open(self.image_filenames[index]) )
         
            return  hr_image

        def __len__(self):
            return len(self.image_filenames)
    

    def hr_transforms():
        return transforms.Compose([
        	# transforms.RandomAffine(degrees=20),
            transforms.Resize((160,160)),
            transforms.ToTensor()
            ])

    scale = transforms.Compose([transforms.ToPILImage(),
                                # transforms.Resize((19,19)),
                                transforms.Resize((20,20)),
                                transforms.ToTensor(),
                                ])
    # transform = transforms.Compose([transforms.Resize((160,160)),
    #                                 transforms.ToTensor()])
    img=TrainDatasetFromFolder(root=opt.dataroot)
    dataloader = torch.utils.data.DataLoader(img, batch_size=opt.batchSize,
                                         shuffle=False, num_workers=int(opt.workers))


    # Set evaluation mode (not training)
    # generator.eval()
    # discriminator.eval()

    for i, (high_res_real) in enumerate(dataloader):
        
        # import ipdb
        # ipdb.set_trace()
        # Downsample images to low resolution
        for j in range(opt.batchSize):
            
            low_res[j] = scale(high_res_real[j])
            high_res_real[j] = high_res_real[j]

        # Generate real and fake inputs
        if opt.cuda:
            high_res_real = Variable(high_res_real.cuda())
            high_res_fake = generator(Variable(low_res).cuda())
        else:
            high_res_real = Variable(high_res_real)
            high_res_fake = generator(Variable(low_res))
        
        

        save_image(high_res_fake[0].data,'/media/ll/ll/lwq/output/fake/'+str(i)+".jpg")
        save_image(low_res[0],'/media/ll/ll/lwq/output/input/'+str(i)+".jpg")
        # avg_psnr=0
        # for k in range(opt.batchSize):
        #     criterion_MSE=nn.MSELoss(size_average=True)
        #     mse = criterion_MSE(high_res_fake[k], high_res_real[k])
        #     psnr = 10 * math.log10(1 / mse.data[0])
        #     avg_psnr += psnr
        # print("======>PSNR:",avg_psnr /opt.batchSize)
        

        # path_high_res_real="/media/ll/ll/lwq/output/7*7/high_res_real"+"/"+str(image_file[i]).split("/")[6]
        # path_high_res_fake="/media/ll/ll/lwq/output/7*7/high_res_fake"+"/"+str(image_file[i]).split("/")[6]
        # path_low_res="/media/ll/ll/lwq/output/7*7/low_res"+"/"+str(image_file[i]).split("/")[6]
     
        
        # if not  os.path.exists(path_high_res_real):
        #     os.makedirs(path_high_res_real)
        # if not  os.path.exists(path_high_res_fake):
        #     os.makedirs(path_high_res_fake)
        # if not  os.path.exists(path_low_res):
        #     os.makedirs(path_low_res)


        # #########    save image   ############
        # save_image(high_res_real[0].data, path_high_res_real +'/'+str(image_file[i]).split("/")[7].split('.')[0] + '.jpg')
        # save_image(high_res_fake[0].data, path_high_res_fake +'/'+ str(image_file[i]).split("/")[7].split('.')[0] + '.jpg')
        # save_image(low_res[0], path_low_res +'/'+str(image_file[i]).split("/")[7].split('.')[0] + '.jpg')

    print("ending ")

