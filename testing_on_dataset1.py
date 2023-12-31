# -*- coding: utf-8 -*-
"""testing_on_dataset1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1uRTIM5iWH8aMetsnDrGTWcS99eX8ZQv_
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

import zipfile
zip_path = '/content/Test_dataset-1.zip'  # Path to the downloaded dataset zip file
output_dir = './'  # Specify the directory where you want to extract the files

# Extract the contents of the zip file
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(output_dir)

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

net=finnalblock(layer_id=0,limit=5,in_channels=1, growth_rate=3, block_config="none", reduction=0.5, drop_rate=0.0)

total_params = sum(p.numel() for p in net.parameters())
print("Total number of parameters: ", total_params)

import torch
import torch.nn as nn

# Create a sample input tensor (assuming input size of 3x32x32)
input_tensor = [torch.randn(1, 1, 100, 100)]

# Enable CUDA if available and move the model and input tensor to the device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = net.cpu()
#input_tensor = input_tensor.to(device)

# Calculate the memory requirement for the model's parameters
param_size = sum(p.numel() for p in model.parameters()) * 4  # Assuming float32 precision (4 bytes per element)

# Perform a forward pass to obtain the intermediate activations and calculate their memory requirement
activations = model([torch.randn(1, 1, 100, 100)],[torch.randn(1, 1, 100, 100)])
activation_size = activations[0].numel() * 4  # Assuming float32 precision (4 bytes per element)


# Calculate the total memory requirement by summing the parameter, activation, and gradient sizes
total_size = param_size + activation_size +0

print("Parameter memory requirement: ", param_size/(1024**2), "MB")
print("Activation memory requirement: ", (activation_size/(1024)*2), "kB")
#/print("Gradient memory requirement: ", grad_size, "bytes")
print("Total memory requirement: ", total_size, "bytes")

import os
import csv

# Set the directory path where the subfolders and images are located
directory_path = "./Test_dataset-1/1_shot_tast_dataset1/quary1"

# Create a CSV file to store the paths and class labels
csv_file = "Query_samples_dataset_one_shot_1.csv"

# Open the CSV file in write mode
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Path", "Class"])  # Write header row

    # Get a list of subfolders in the main directory
    subfolders = sorted([f.path for f in os.scandir(directory_path) if f.is_dir()])

    # Assign numeric class labels
    class_labels = range(len(subfolders))
    ix=0

    # Iterate over each subfolder and its corresponding class label
    for class_label, subfolder in zip(class_labels, subfolders):
        # Get a list of image files in the current subfolder
        image_files = [f.path for f in os.scandir(subfolder) if f.is_file() and f.name.endswith((".jpg", ".jpeg", ".png"))]

        image_files = image_files

        for image_file in image_files:
            image = Image.open(image_file)

            writer.writerow([image_file, ix])
        ix=ix+1

import os
import csv

# Set the directory path where the subfolders and images are located
directory_path = "./Test_dataset-1/2_shot_tast_dataset1/quary2"

# Create a CSV file to store the paths and class labels
csv_file = "Query_samples_dataset_one_shot_2.csv"

# Open the CSV file in write mode
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Path", "Class"])  # Write header row

    # Get a list of subfolders in the main directory
    subfolders = sorted([f.path for f in os.scandir(directory_path) if f.is_dir()])

    # Assign numeric class labels
    class_labels = range(len(subfolders))
    ix=0

    # Iterate over each subfolder and its corresponding class label
    for class_label, subfolder in zip(class_labels, subfolders):
        # Get a list of image files in the current subfolder
        image_files = [f.path for f in os.scandir(subfolder) if f.is_file() and f.name.endswith((".jpg", ".jpeg", ".png"))]

        image_files = image_files

        for image_file in image_files:
            image = Image.open(image_file)

            writer.writerow([image_file, ix])
        ix=ix+1

import os
import csv

# Set the directory path where the subfolders and images are located
directory_path = "./Test_dataset-1/3_shot_tast_dataset1/quary3"

# Create a CSV file to store the paths and class labels
csv_file = "Query_samples_dataset_one_shot_3.csv"

# Open the CSV file in write mode
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Path", "Class"])  # Write header row

    # Get a list of subfolders in the main directory
    subfolders = sorted([f.path for f in os.scandir(directory_path) if f.is_dir()])

    # Assign numeric class labels
    class_labels = range(len(subfolders))
    ix=0

    # Iterate over each subfolder and its corresponding class label
    for class_label, subfolder in zip(class_labels, subfolders):
        # Get a list of image files in the current subfolder
        image_files = [f.path for f in os.scandir(subfolder) if f.is_file() and f.name.endswith((".jpg", ".jpeg", ".png"))]

        image_files = image_files

        for image_file in image_files:
            image = Image.open(image_file)

            writer.writerow([image_file, ix])
        ix=ix+1

import os
import csv

# Set the directory path where the subfolders and images are located
directory_path = "./Test_dataset-1/4_shot_tast_dataset1/quary4"

# Create a CSV file to store the paths and class labels
csv_file = "Query_samples_dataset_one_shot_4.csv"

# Open the CSV file in write mode
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Path", "Class"])  # Write header row

    # Get a list of subfolders in the main directory
    subfolders = sorted([f.path for f in os.scandir(directory_path) if f.is_dir()])

    # Assign numeric class labels
    class_labels = range(len(subfolders))
    ix=0

    # Iterate over each subfolder and its corresponding class label
    for class_label, subfolder in zip(class_labels, subfolders):
        # Get a list of image files in the current subfolder
        image_files = [f.path for f in os.scandir(subfolder) if f.is_file() and f.name.endswith((".jpg", ".jpeg", ".png"))]

        image_files = image_files

        for image_file in image_files:
            image = Image.open(image_file)

            writer.writerow([image_file, ix])
        ix=ix+1

import os
import csv

# Set the directory path where the subfolders and images are located
directory_path = "./Test_dataset-1/5_shot_tast_dataset1/quary5"

# Create a CSV file to store the paths and class labels
csv_file = "Query_samples_dataset_one_shot_5.csv"

# Open the CSV file in write mode
with open(csv_file, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Path", "Class"])  # Write header row

    # Get a list of subfolders in the main directory
    subfolders = sorted([f.path for f in os.scandir(directory_path) if f.is_dir()])

    # Assign numeric class labels
    class_labels = range(len(subfolders))
    ix=0

    # Iterate over each subfolder and its corresponding class label
    for class_label, subfolder in zip(class_labels, subfolders):
        # Get a list of image files in the current subfolder
        image_files = [f.path for f in os.scandir(subfolder) if f.is_file() and f.name.endswith((".jpg", ".jpeg", ".png"))]

        image_files = image_files

        for image_file in image_files:
            image = Image.open(image_file)

            writer.writerow([image_file, ix])
        ix=ix+1

def imshow(img,text=None,should_save=False):
    npimg = img.numpy()
    plt.axis("off")
    if text:
        plt.text(75, 8, text, style='italic',fontweight='bold',
            bbox={'facecolor':'white', 'alpha':0.8, 'pad':10})
    plt.imshow(np.transpose(npimg, (1, 2, 0)))
    plt.show()

def show_plot(iteration,loss):
    plt.plot(iteration,loss)
    plt.show()
import csv
import random

import csv
import random

def get_neg_img(csv_file, class_excluded):
    with open(csv_file, "r") as file:
        csv_reader = csv.DictReader(file)
        rows = [row for row in csv_reader if row['Class'] != str(class_excluded)]
        random_row = random.choice(rows)
        return random_row['Path'], random_row['Class']

import os
from PIL import Image
import statistics
from collections import defaultdict

def load_images_from_folder(parent_folder, folder_name):
    folder_path = os.path.join(parent_folder, folder_name)
    images = []

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"Folder '{folder_name}' not found in '{parent_folder}'.")
        return images

    with Pool() as pool:
        file_paths = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, filename))]
        images = pool.map(load_image, file_paths)

    return [img for img in images if img is not None]

import torch
import time
from skimage import exposure
from multiprocessing import Pool



from skimage import exposure
from multiprocessing import Pool
def Testdataset1_in_one_shot(threshold, Qcsv, supportpdroot):
    transform = transforms.Compose([
        transforms.Resize((100, 100)),
        transforms.ToTensor()
    ])
    csv_file = Qcsv
    count = 0
    total = 0
    similarities = []
    associative_array = defaultdict(list)
    associative_array_all = defaultdict(list)

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row

        for row in reader:
            image_path, class_label = row
            image = Image.open(image_path).convert("L")

            max_similarity, avg_similarity = comparenewF(image, class_label, threshold, supportpdroot)
            key = class_label
            value = avg_similarity
            all_key=str(class_label)+str(class_label)
            associative_array[key].append(value)
            similarities.append(avg_similarity)
           # print(class_label,max_similarity,image_path)
            if max_similarity >= threshold:
              print(class_label,image_path,"was successfully classified")
              all_key=str(class_label)+str(class_label)
              associative_array_all[all_key].append(value)
              count += 1
            else:
              all_key=str(class_label)+str(class_label)+"negative"
              associative_array_all[all_key].append(value)
            total += 1

            neg_img_pt, neg_clss = get_neg_img(csv_file, class_label)

            neg_img = Image.open(neg_img_pt).convert("L")
            max_ave_similarity, neg_avg_similarity = comparenewF(neg_img, class_label, threshold, supportpdroot)

            if max_ave_similarity < threshold:
                all_key=str(class_label)+str(neg_clss)
                associative_array_all[all_key].append(value)
                count += 1
            else:
              all_key=str(class_label)+str(neg_clss)+"negative"
              associative_array_all[all_key].append(value)

            total += 1

    print("\nAverage similarity score of the full dataset:", sum(similarities) / len(similarities))
   # print("Threshold:", threshold, "Accuracy:", count/total, "%", count, total)

    std_dev_values = {}
    for key, values in associative_array.items():
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        print(f"class: {key}, Mean ± SD: {mean:.5f} ± {std_dev:.5f}")

    return count/total,associative_array_all

def comparenewF(qurimg, label22, threshold, supportpdroot):
    transform = transforms.Compose([
         transforms.Resize((100, 100)),
        transforms.ToTensor()
    ])

    parent_location = supportpdroot
    subfolder_name = label22

    loaded_support_class_images = load_images_from_folder(parent_location, subfolder_name)

    qurimg = preprocessff(qurimg)
    qurimg = transform(qurimg)
    qurimg = qurimg.unsqueeze(0)
    similarity_scores_list = []

    for s_image in loaded_support_class_images:
        s_image = preprocessff(s_image)
        s_image = transform(s_image)
        s_image = s_image.unsqueeze(0)

        concatenated = torch.cat((s_image, qurimg), 0)

        x0, x1 = s_image, qurimg
        #x0, x1 = s_image.cuda(), qurimg.cuda()

        net.eval()
        with torch.no_grad():
            output1, output2 = net([x0], [x1])

            flat_list1 = torch.cat([tensor.flatten() for tensor in output1])
            flat_list2 = torch.cat([tensor.flatten() for tensor in output2])

            cos = F.cosine_similarity(flat_list1.unsqueeze(0), flat_list2.unsqueeze(0))
            similarity_scores_list.append(cos.item())

    return max(similarity_scores_list), sum(similarity_scores_list) / len(similarity_scores_list)
from collections import defaultdict
from torchvision.transforms import ToTensor
from torchvision.models import resnet18
from multiprocessing import Pool
def load_image(file_path):
    try:
        img = Image.open(file_path).convert("L")
        return img
    except Exception as e:
        print(f"Error loading image: {file_path} - {e}")
        return None
from PIL import Image, ImageOps
from PIL import ImageFilter
def preprocessff(image):

      transform = transforms.Compose([
          transforms.Resize((100,100)),
          transforms.ToTensor()

      ])

      return  image

def Testdataset1_in_few_shot(shot,threshold, Qcsv, supportpdroot):
    transform = transforms.Compose([
        transforms.Resize((100, 100)),
        transforms.ToTensor()
    ])
    csv_file = Qcsv
    count = 0
    total = 0
    similarities = []
    associative_array = defaultdict(list)
    associative_array_all = defaultdict(list)

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row

        for row in reader:
            image_path, class_label = row
            image = Image.open(image_path).convert("L")
            similarity_lst, avg_similarity = comparenewFfs(image, class_label, threshold, supportpdroot)
            support = len([item for item in similarity_lst if item >= threshold])
            key = class_label
            value = avg_similarity
            #all_key=str(class_label)+str(class_label)
            associative_array[key].append(value)
            similarities.append(avg_similarity)
           #print(class_label,support,image_path)
            if support >= int((shot+1)/2):
                print(class_label,image_path,"was successfully classified")
                all_key=str(class_label)+str(class_label)
                associative_array_all[all_key].append(value)
                count += 1
            else:
              all_key=str(class_label)+str(class_label)+"negative"
              associative_array_all[all_key].append(value)
            total += 1

            neg_img_pt, neg_clss = get_neg_img(csv_file, class_label)

            neg_img = Image.open(neg_img_pt).convert("L")
            similarity_nlst, neg_avg_similarity = comparenewFfs(neg_img, class_label, threshold, supportpdroot)
            support_n = len([item for item in similarity_nlst if item >= threshold])

            if support_n < int((shot+1)/2):
                all_key=str(class_label)+str(neg_clss)
                associative_array_all[all_key].append(value)
                count += 1
            else:
              all_key=str(class_label)+str(neg_clss)+"negative"
              associative_array_all[all_key].append(value)

            total += 1

    print("\nAverage similarity score of the full dataset:", sum(similarities) / len(similarities))
    #print("Threshold:", threshold, "Accuracy:", count/total, "%", count, total)

    std_dev_values = {}
    for key, values in associative_array.items():
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        print(f"class: {key}, Mean ± SD: {mean:.5f} ± {std_dev:.5f}")

    return count/total,associative_array_all

def comparenewFfs(qurimg, label22, threshold, supportpdroot):
    transform = transforms.Compose([
         transforms.Resize((100, 100)),
        transforms.ToTensor()
    ])

    parent_location = supportpdroot
    subfolder_name = label22

    loaded_support_class_images = load_images_from_folder(parent_location, subfolder_name)

    qurimg = preprocessff(qurimg)
    qurimg = transform(qurimg)
    qurimg = qurimg.unsqueeze(0)
    similarity_scores_list = []

    for s_image in loaded_support_class_images:
        s_image = preprocessff(s_image)
        s_image = transform(s_image)
        s_image = s_image.unsqueeze(0)

#        concatenated = torch.cat((s_image, qurimg), 0)
       # x0, x1 = s_image.cuda(), qurimg.cuda()
        x0, x1 = s_image, qurimg
        net.eval()
        with torch.no_grad():
            output1, output2 = net([x0], [x1])

            flat_list1 = torch.cat([tensor.flatten() for tensor in output1])
            flat_list2 = torch.cat([tensor.flatten() for tensor in output2])

            cos = F.cosine_similarity(flat_list1.unsqueeze(0), flat_list2.unsqueeze(0))
            similarity_scores_list.append(cos.item())

    return similarity_scores_list, sum(similarity_scores_list) / len(similarity_scores_list)

def calculate_f1_score(tp, fp, fn, tn):

# Calculate precision
    if tp + fp == 0:
        precision = 0  # Set precision to 0 when the denominator is zero
    else:
        precision = tp / (tp + fp)

    # Calculate recall
    if tp + fn == 0:
        recall = 0  # Set recall to 0 when the denominator is zero
    else:
        recall = tp / (tp + fn)

    if precision + recall == 0:
        f1_score = 0
    else:
        f1_score = 2 * (precision * recall) / (precision + recall)
    return f1_score
def f1_csv(pathh,arar,accuracy,th,shot,dataset):
  file_path ="./"+pathh  # Replace with the desired file path
  with open(file_path, 'a') as file:
      # Write lines to the file
      a="\n\n\n\n----------------------------------------------------------\n----------------------------------------------------------------\n\n\n"+"Threshold:"+str(th)+"\n Accuracy: "+str(accuracy)+"%"+"\n Dataset: "+str(dataset)+"\n Shot: "+str(shot)
     # b="\n tp: "+str(tp)+", fp: "+str(fp)+", fn:"+str(fn)+", tn: "+str(tn)+"\n  "
      file.write(a)

      file.write("\n")
# print(arar)
# for each in arar:
      #   print(each,":",len(arar[each]))
      tpo=0
      tno=0
      fpo=0
      fno=0
      for i in range(0,10):
        file.write(str("\n \n for class "+str(i)))
        tp=0
        tn=0
        fp=0
        fn=0
        if str(i)+str(i) in arar:
            tp+=len(arar[str(i)+str(i)])
        if str(i)+str(i)+"negative" in arar:
            fn+=len(arar[str(i)+str(i)+"negative"])
        for j in [k for k in range(0, 10) if k != i]:

          if str(i)+str(j) in arar:
            tn+=len(arar[str(i)+str(j)])
          # if str(j)+str(i) in arar:
          #   tn+=len(arar[str(j)+str(i)])


          if str(i)+str(j)+"negative" in arar:
            fp+=len(arar[str(i)+str(j)+"negative"])
        # print(tp,tn,fp,fn)
          # if str(j)+str(i)+"negative" in arar:
          #   fp+=len(arar[str(i)+str(j)+"negative"])
        print(tp,tn,fp,fn,tp+tn+fp+fn,calculate_f1_score(tp, fp, fn, tn))

        file.write(str("\n f1 score:"+str(calculate_f1_score(tp, fp, fn, tn))))
        tpo+=tp
        tno+=tn
        fpo+=fp
        fno+=fn
      b="\n tp: "+str(tpo)+", fp: "+str(fpo)+", fn:"+str(fno)+", tn: "+str(tno)+"\n  "
      file.write(b)

net.load_state_dict(torch.load('_model_',map_location=torch.device('cpu')))

for i in range(0,5):
  accu,arar=Testdataset1_in_one_shot(.82,"./Query_samples_dataset_one_shot_1.csv", './Test_dataset-1/1_shot_tast_dataset1/support1')
  f1_csv("Dataset1_one_shot_result.txt",arar,accu*100,0.82,1,"Normal_dristibution")

for i in range(0,5):
  accu,arar=Testdataset1_in_few_shot(2,.82,"./Query_samples_dataset_one_shot_2.csv", './Test_dataset-1/2_shot_tast_dataset1/support2')
  f1_csv("Dataset1_two_shot_result.txt",arar,accu*100,0.82,2,"Normal_dristibution")

for i in range(0,5):
  accu,arar=Testdataset1_in_few_shot(3,.82,"./Query_samples_dataset_one_shot_3.csv", './Test_dataset-1/3_shot_tast_dataset1/support3')
  f1_csv("Dataset1_three_shot_result.txt",arar,accu*100,0.82,3,"Normal_dristibution")

for i in range(0,5):
  accu,arar=Testdataset1_in_few_shot(4,.82,"./Query_samples_dataset_one_shot_4.csv", './Test_dataset-1/4_shot_tast_dataset1/support4')
  f1_csv("Dataset1_four_shot_result.txt",arar,accu*100,0.82,4,"Normal_dristibution")

for i in range(0,5):
  accu,arar=Testdataset1_in_few_shot(5,.82,"./Query_samples_dataset_one_shot_5.csv", './Test_dataset-1/5_shot_tast_dataset1/support5')
  f1_csv("Dataset1_five_shot_result.txt",arar,accu*100,0.82,5,"Normal_dristibution")