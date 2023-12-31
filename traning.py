# -*- coding: utf-8 -*-
"""traning.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/11uVFAsKXeQVTyHkd8oKINwAEW300fK5D
"""

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
import torchvision
import torchvision.datasets as dset
import torchvision.transforms as transforms
from torch.utils.data import DataLoader,Dataset
import matplotlib.pyplot as plt
import torchvision.utils
import numpy as np
import random
from PIL import Image
import torch
from torch.autograd import Variable
import PIL.ImageOps
import torch.nn as nn
from torch import optim
import torch.nn.functional as F

class Config():
    training_dir = "/content/dtrain"
    testing_dir = '/content/val'
    train_batch_size = 64
    train_number_epochs = 100
folder_dataset = dset.ImageFolder(root=Config.training_dir)

class SiameseNetworkDataset(Dataset):

    def __init__(self,imageFolderDataset,transform=None,should_invert=False,validation=0):
        self.imageFolderDataset = imageFolderDataset
        self.should_invert=should_invert
        self.validation=validation
        self.transform =transforms.Compose([
            transforms.Resize((100,100)),
            transforms.RandomRotation(degrees=15),
            transforms.RandomHorizontalFlip(),
            transforms.RandomResizedCrop(size=100, scale=(0.8, 1.0)),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.1),
            transforms.ToTensor()
        ])
        self.transform_val =transforms.Compose([
            transforms.Resize((100,100)),
            transforms.ToTensor()
                ])

    def __getitem__(self,index):
        img0_tuple = random.choice(self.imageFolderDataset.imgs)
        #we need to make sure approx 50% of images are in the same class
        should_get_same_class = random.randint(0,1)
        if should_get_same_class:
            while True:
                #keep looping till the same class image is found
                img1_tuple = random.choice(self.imageFolderDataset.imgs)
                if img0_tuple[1]==img1_tuple[1]:
                    break
        else:
            while True:
                #keep looping till a different class image is found

                img1_tuple = random.choice(self.imageFolderDataset.imgs)
                if img0_tuple[1] !=img1_tuple[1]:
                    break

        img0 = Image.open(img0_tuple[0])
        img1 = Image.open(img1_tuple[0])
        img0 = img0.convert("L")
        img1 = img1.convert("L")

        if self.should_invert:
            img0 = PIL.ImageOps.invert(img0)
            img1 = PIL.ImageOps.invert(img1)

      #  if self.transform is not None:
        if(self.validation==0):
          img0 = self.transform(img0)
          img1 = self.transform(img1)
        else:
          img0 = self.transform_val(img0)
          img1 = self.transform_val(img1)

        return img0, img1 , torch.from_numpy(np.array([int(img1_tuple[1]!=img0_tuple[1])],dtype=np.float32))

    def __len__(self):
        return len(self.imageFolderDataset.imgs)

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class BasicBlock1(nn.Module):
    def __init__(self, in_planes, out_planes, dropRate=0.0):
        super(BasicBlock1, self).__init__()
        self.bn1 = nn.BatchNorm2d(out_planes)
        self.relu = nn.ReLU(inplace=True)
        self.padd=nn.ReflectionPad2d(2)
        self.conv1 = nn.Conv2d(in_planes, out_planes, kernel_size=3, stride=2,
                               bias=False)

        self.droprate = dropRate
    def forward(self, x):
        out = self.relu(self.bn1(self.conv1(self.padd(x))))
        if self.droprate > 0:
            out = F.dropout(out, p=self.droprate, training=self.training)
        return out



class BasicBlock2Resnet(nn.Module):
    def __init__(self, in_channels,groth, stride=1,dropRate=0.0):
        super(BasicBlock2Resnet, self).__init__()
        self.padd=nn.ReflectionPad2d(2)
        self.conv1 = nn.Conv2d(in_channels, groth, kernel_size=3, stride=2, padding=0, bias=False)
        self.bn1 = nn.BatchNorm2d(groth)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(groth, groth, kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(groth)
        self.dropout = nn.Dropout2d(p=dropRate)



        self.conv1r = nn.Conv2d(in_channels, groth, kernel_size=3, stride=2, padding=0, bias=False)
        self.bn1r = nn.BatchNorm2d(groth)
        self.droprate = dropRate



    def forward(self, x):
        residual = x
        residual=self.padd(x)

        out = self.conv1(residual)
        out = self.bn1(out)
        out = self.relu(out)

        if self.droprate > 0:
            out = F.dropout(out, p=self.droprate, training=self.training)

        out1=out




        out = self.conv2(out)
        out = self.bn2(out)
        if self.droprate > 0:
            out = F.dropout(out, p=self.droprate, training=self.training)

        oresidualut = self.conv1r(residual)
        oresidualut = self.bn1r(oresidualut)
        oresidualut = self.relu(oresidualut)
        if self.droprate > 0:
            oresidualut = F.dropout(oresidualut, p=self.droprate, training=self.training)
        out =torch.cat([out, oresidualut],1)
        out = self.relu(out)
        return out



import torch
import torch.nn as nn
import math

class BottleneckLayer(nn.Module):
    def __init__(self, in_channels, growth_rate, drop_rate):
        super(BottleneckLayer, self).__init__()
        self.bn1 = nn.BatchNorm2d(in_channels)
        self.relu1 = nn.ReLU(inplace=True)
        self.conv1 = nn.Conv2d(in_channels, 4 * growth_rate, kernel_size=1, bias=False)
        self.bn2 = nn.BatchNorm2d(4 * growth_rate)
        self.relu2 = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(4 * growth_rate, growth_rate, kernel_size=3, padding=1, bias=False)
        self.drop_rate = drop_rate

    def forward(self, x):
        out = self.relu1(self.bn1(x))
        out = self.conv1(out)
        if self.drop_rate > 0:
          out = F.dropout(out, p=self.drop_rate, training=self.training)
        out = self.relu2(self.bn2(out))
        out = self.conv2(out)
        out = torch.cat((x, out), 1)  # Concatenate the input with the output feature maps
        if self.drop_rate > 0:
            out = F.dropout(out, p=self.drop_rate, training=self.training)
        return out

class DenseBlock(nn.Module):
    def __init__(self, in_channels, growth_rate, num_layers, reduction=0.5, drop_rate=0.0):
        super(DenseBlock, self).__init__()
        layers = []
        for i in range(num_layers):
            layers.append(BottleneckLayer(in_channels + i * growth_rate, growth_rate, drop_rate))
        self.layers = nn.Sequential(*layers)

    def forward(self, x):
        out = self.layers(x)

        return out

class DenseNetm(nn.Module):
    def __init__(self, in_channels, growth_rate, reduction=0.5, drop_rate=0.0):
        super(DenseNetm, self).__init__()
        self.in_channels = in_channels
        self.drop_rate=drop_rate
        self.conv1 = nn.Conv2d(in_channels, in_channels, kernel_size=3, stride=2, padding=0, bias=False)
        self.bn1 = nn.BatchNorm2d(in_channels)
        self.relu = nn.ReLU(inplace=True)
        self.padd = nn.ReflectionPad2d(2)
        self.block = DenseBlock(self.in_channels, growth_rate, 3, reduction, drop_rate)
        self.outcnl = in_channels + 3 * growth_rate
        self.convout = nn.Conv2d(math.floor((in_channels + 3 * growth_rate)),  2 * growth_rate, kernel_size=1, bias=False)
        self.bn1out = nn.BatchNorm2d(2 * growth_rate)

    def forward(self, x):
        x = self.padd(x)
        out = self.conv1(x)
        if self.drop_rate > 0:
          out = F.dropout(out, p=self.drop_rate, training=self.training)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.block(out)
        out = self.convout(out)
        if self.drop_rate > 0:
          out = F.dropout(out, p=self.drop_rate, training=self.training)

        out = self.bn1out(out)
        out = self.relu(out)

        return out






class Eachnode(nn.Module):
    def __init__(self, in_channels, growth_rate, block_config="none", reduction=0.5, drop_rate=0.0):
        super(Eachnode, self).__init__()

        self.Basiccblock = BasicBlock1(in_planes=in_channels, out_planes=2*growth_rate, dropRate=drop_rate)
        self.Resblock = BasicBlock2Resnet(in_channels,groth=growth_rate,  dropRate=drop_rate)
        self.Densblock = DenseNetm(in_channels,growth_rate, reduction,drop_rate)


    def forward(self, x):

        out1 = self.Basiccblock(x)
        out2 = self.Resblock(x)
        out3 = self.Densblock(x)




        return [out1,out2,out3]


import torch.nn as nn

def create_fc_layer(in_features, out_features, activation=None, dropout_rate=0.0):
    layer = nn.Linear(in_features, out_features)

    layers = [layer]
    if activation is not None:
        if activation == 'relu':
            activation_layer = nn.ReLU(inplace=True)
        elif activation == 'sigmoid':
            activation_layer = nn.Sigmoid()
        elif activation == 'tanh':
            activation_layer = nn.Tanh()
        else:
            raise ValueError("Invalid activation specified.")

        layers.append(activation_layer)

    if dropout_rate > 0.0:
        dropout_layer = nn.Dropout(p=dropout_rate)
        layers.append(dropout_layer)

    return nn.Sequential(*layers)

class ThreeLayerFC(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, activation='relu', dropout_rate=0.0):
        super(ThreeLayerFC, self).__init__()
        self.fc1 = create_fc_layer(input_size, hidden_size, activation, dropout_rate)
        self.fc2 = create_fc_layer(hidden_size, hidden_size, activation, dropout_rate)
        self.fc3 = create_fc_layer(hidden_size, output_size)

    def forward(self, x):
        x = self.fc1(x)
        x = self.fc2(x)
        x = self.fc3(x)
        return x



import math

import math
import torch
import torch.nn as nn

class finnalblock(nn.Module):
    def __init__(self, layer_id, limit, in_channels, growth_rate, block_config="none", reduction=0.5, drop_rate=0.0):
        super(finnalblock, self).__init__()
        self.layer =nn.ModuleList()
        self.layer_id = layer_id
        self.limit = limit
        self.growth_rate = growth_rate
        self.in_channels = in_channels
        self.diamension=100
        lid = self.layer_id
        for i in range(int(self.limit)):
            self.diamension=math.floor((self.diamension - 3 + 2 * 2) / 2) + 1
            for j in range(int(math.pow(3, i))):
                self.layer.append(Eachnode(self.in_channels, growth_rate=self.growth_rate, block_config="none", reduction=reduction, drop_rate=drop_rate))
            lid += 1
            self.in_channels = 2 * self.growth_rate
            self.growth_rate = self.growth_rate * 2

        self.fcs = nn.ModuleList()
        for j in range(int(math.pow(3, self.limit))):
            self.fcs.append(ThreeLayerFC(input_size=self.diamension*self.diamension*self.growth_rate, hidden_size=50, output_size=2, activation='relu', dropout_rate=drop_rate))

    def forward_once(self, x):
        out = []
        lid = 0
        for i in range(int(self.limit)):
            out = []
            for j in range(int(math.pow(3, i))):
                kk = self.layer[lid](x[j])
                for each in kk:
                    out.append(each)
                lid += 1
            x = out
        out = []
        for j in range(int(math.pow(3, self.limit))):
            jj = self.fcs[j](x[j].view(x[j].size()[0], -1))
            out.append(jj)

        return torch.stack(out)

    def forward(self, input1, input2):
        output1 = self.forward_once(input1)
        output2 = self.forward_once(input2)
        return output1, output2

class Config():
    training_dir = "/content/dtrain"
    testing_dir = '/content/val'
    train_batch_size = 64
    train_number_epochs = 100
folder_dataset = dset.ImageFolder(root=Config.training_dir)
siamese_dataset = SiameseNetworkDataset(imageFolderDataset=folder_dataset,
                                        transform=transforms.Compose([transforms.Resize((100,100)),
                                                                      transforms.ToTensor()
                                                                      ])
                                       ,should_invert=False,validation=0)

folder_dataset_val= dset.ImageFolder(root=Config.testing_dir)
siamese_dataset_val=SiameseNetworkDataset(imageFolderDataset=folder_dataset_val,
                                        transform=transforms.Compose([transforms.Resize((100,100)),
                                                                      transforms.ToTensor()
                                                                      ])
                                       ,should_invert=False,validation=1)

vis_dataloader = DataLoader(siamese_dataset,
                        shuffle=True,
                        num_workers=8,
                        batch_size=8)

train_dataloader = DataLoader(siamese_dataset,
                        shuffle=True,
                        num_workers=8,
                        batch_size=60)
val_dataloader = DataLoader(siamese_dataset_val,
                        shuffle=True,
                        num_workers=8,
                        batch_size=20)

net=finnalblock(layer_id=0,limit=5,in_channels=1, growth_rate=3, block_config="none", reduction=0.5, drop_rate=0.15)
net=net.cuda()
optimizer = optim.Adam(net.parameters(),lr = 0.009 )

class ContrastiveLoss12(torch.nn.Module):
    """
    Contrastive loss function.
    Based on: http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    """

    def __init__(self, margin=2.0):
        super(ContrastiveLoss12, self).__init__()
        self.margin = margin

    def forward(self, output1, output2, label):
        euclidean_distance = F.pairwise_distance(output1, output2, keepdim = True)
        loss_contrastive = torch.mean((1-label) * torch.pow(euclidean_distance, 2) +
                                      (label) * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2))


        return loss_contrastive

criterion2 = ContrastiveLoss12()

counter = []
loss_history = []
iteration_number= 0

def csv_write(fname, new_row):
  import csv

  csv_filename = fname
  with open(csv_filename, mode='a', newline='') as file:
      writer = csv.writer(file)
      writer.writerow(new_row)

def val(nett,epoch):
  nett.eval()  # Set the network to evaluation mode
  with torch.no_grad():  # Disable gradient calculation during validation
    validation_loss = 0.0
    total_samples = 0
    correct_predictions = 0

    for i, data in enumerate(val_dataloader, 0):
        img0, img1, label = data
        img0, img1, label = img0.cuda(), img1.cuda(), label.cuda()

        output1, output2 = nett([img0], [img1])
        loss_contrastive = criterion2(output1, output2, label)
        validation_loss += loss_contrastive.item() * img0.size(0)
        total_samples += img0.size(0)

        # Calculate accuracy

    average_validation_loss = validation_loss / total_samples
   # accuracy = correct_predictions / total_samples
  print("Validation loss: {}".format(average_validation_loss))
  #print("Accuracy: {:.2%}".format(accuracy))
  csv_write('./validation_loss.csv',[epoch, average_validation_loss])
  return average_validation_loss

val_loss=50
for epoch in range(1,500):
    net.train()
    epoch_loss=[]
    for i, data in enumerate(train_dataloader,0):
        img0, img1 , label = data
        img0, img1 , label = img0.cuda(), img1.cuda() , label.cuda()
        optimizer.zero_grad()
        output1,output2 = net([img0],[img1])
        loss_contrastive = criterion2(output1,output2,label)
        loss_contrastive.backward()
        epoch_loss.append(loss_contrastive.item())
        optimizer.step()
        if i %10 == 0 :
            print("Epoch number {}\n Current loss {}\n".format(epoch,loss_contrastive.item()))
            iteration_number +=10
            counter.append(iteration_number)
            loss_history.append(loss_contrastive.item())
    tmp_val_loss=val(net,epoch)
    if(val_loss > tmp_val_loss):
      val_loss=tmp_val_loss
      torch.save(net.state_dict(), '_model_.pth')

    csv_write('./train_loss.csv',[epoch, sum(epoch_loss)/len(epoch_loss)])

