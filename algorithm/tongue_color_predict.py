import torch
import torch.nn as nn
import torch.optim as optim
from algorithm.lenet import LeNet5
from utils.imageloader import Dataloader
import time
from PIL import Image
import numpy as np
import base64


def prediction(img_file_path):
    img = Image.open(img_file_path)
    img_resize = img.resize((128, 128))
    img_np = np.array(img_resize).transpose((2, 1, 0))
    img = torch.tensor([img_np])

    model_tongue = LeNet5(num_types=4)
    model_tongue.load_state_dict(torch.load('./files/LeNet_togue_color_predict.pt'))
    output = model_tongue(img.float())
    pred_tongue_label = output.detach().max(1)[1]
    tongue_colors = {0:'淡红', 1:'淡白', 2:'红', 3:'暗紫'}
    pred_tongue_color = tongue_colors[int(pred_tongue_label)]

    model_moss = LeNet5(num_types=2)
    model_moss.load_state_dict(torch.load('./files/LeNet_moss_color_predict.pt'))
    output = model_moss(img.float())
    pred_moss_label = output.detach().max(1)[1]
    moss_colors = {0: '白', 1: '黄'}
    pred_moss_color = moss_colors[int(pred_moss_label)]

    return pred_tongue_color, pred_moss_color

def batch_prediction(num):
    image_folder_path = './static/data/tongueimage'
    label_path = './files/tongue_all_features.csv'
    dataloader = Dataloader(image_folder_path, label_path)

    patient_ids, images, tongue_colors, moss_colors = dataloader.get_datainstance()
    # 随机采样num个数据
    sample_ids = []
    sample_imgs = []
    sample_tongue_colors = []
    sample_moss_colors = []
    sample_img_paths = []
    rds = []
    for i in range(num):
        rd = np.random.randint(0, len(patient_ids))
        while rd in rds:
            rd = np.random.randint(0, len(patient_ids))
        sample_ids.append(patient_ids[rd])
        sample_imgs.append(images[rd])
        sample_tongue_colors.append(tongue_colors[rd])
        sample_moss_colors.append(moss_colors[rd])
        sample_img_paths.append("static/data/tongueimage/" + patient_ids[rd].lower() + ".bmp")
        rds.append(rd)

    sample_images_tensor = torch.LongTensor(sample_imgs)
    sample_tongue_colors_tensor = torch.LongTensor(sample_tongue_colors)
    sample_moss_colors_tensor = torch.LongTensor(sample_moss_colors)

    model_tongue = LeNet5(num_types=4)
    model_tongue.load_state_dict(torch.load('./files/LeNet_togue_color_predict.pt'))
    outputs = model_tongue(sample_images_tensor.float())
    pred_tongue_labels = outputs.detach().max(1)[1]
    tongue_color_correct = pred_tongue_labels.eq(sample_tongue_colors_tensor).sum()
    tongue_color_accuracy = float(tongue_color_correct) / num
    tongue_colors = {0: '淡红', 1: '淡白', 2: '红', 3: '暗紫'}
    true_tongue_colors = []
    pred_tongue_colors = []
    for i in range(num):
        true_tongue_colors.append(tongue_colors[sample_tongue_colors[i]])
        pred_tongue_colors.append(tongue_colors[int(pred_tongue_labels[i])])
    # print(sample_tongue_colors, pred_tongue_labels)
    # print(true_tongue_colors, pred_tongue_colors)

    model_moss = LeNet5(num_types=2)
    model_moss.load_state_dict(torch.load('./files/LeNet_moss_color_predict.pt'))
    outputs = model_moss(sample_images_tensor.float())
    pred_moss_labels = outputs.detach().max(1)[1]
    moss_color_correct = pred_moss_labels.eq(sample_moss_colors_tensor).sum()
    moss_color_accuracy = float(moss_color_correct) / num
    moss_colors = {0: '白', 1: '黄'}
    true_moss_colors = []
    pred_moss_colors = []
    for i in range(num):
        true_moss_colors.append(moss_colors[sample_moss_colors[i]])
        pred_moss_colors.append(moss_colors[int(pred_moss_labels[i])])

    results = {
        'sample_ids': sample_ids,
        'sample_img_paths': sample_img_paths,
        'true_tongue_colors': true_tongue_colors,
        'pred_tongue_colors': pred_tongue_colors,
        'true_moss_colors': true_moss_colors,
        'pred_moss_colors': pred_moss_colors,
        'tongue_color_accuracy': tongue_color_accuracy,
        'moss_color_accuracy': moss_color_accuracy
    }
    # print(results)
    return results


def img_stream(img_local_path):
    with open(img_local_path, 'rb') as img_f:
        img_stream = img_f.read()
        img_stream = base64.b64encode(img_stream).decode()
    return img_stream


def train(model, train_loader, lr, epoch):
    model.train()
    loss_func = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    total_loss = 0
    train_times = 0
    t1 = time.time()
    for batch_id, (batch_imgs, batch_labels) in enumerate(train_loader):
        t2 = time.time()
        output = model(batch_imgs.float())

        loss = loss_func(output, batch_labels)
        total_loss += loss.item()
        train_times += 1

        # 更新模型
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        # print('Epoch:{} batch:{} time_cost:{:.2f}s loss:{:.6f}'.format(epoch, batch_id, time.time() - t2, loss.item()))

    if epoch % 10 == 0:
        print('|Epoch:{} end, training_time_cost:{:.2f}s total_loss:{:.6f}'.format(epoch, time.time() - t1, total_loss / train_times))

def test(model, test_loader, epoch):
    model.eval()
    total_correct = 0
    test_num = 0
    for batch_id, (batch_imgs, batch_labels) in enumerate(test_loader):
        output = model(batch_imgs.float())
        pred_labels = output.detach().max(1)[1]
        total_correct += pred_labels.eq(batch_labels.view_as(pred_labels)).sum()
        test_num += len(pred_labels)
        if epoch == 99:
            print('true_label:',batch_labels, '---> pred_label:',pred_labels)

        # print(batch_id, pred_labels, len(pred_labels))
    accuracy = float(total_correct) / test_num
    print('Test epoch:{}| Accuracy:{:.6f}'.format(epoch, accuracy))
    return accuracy


if __name__ == '__main__':
    num_epoch = 100
    batch_size = 16
    input_size = 128
    lr = 2e-3

    # 舌色预测
    # image_folder_path = '../static/data/tongueimage_aug'
    # label_path = '../files/tongue_all_features_aug.csv'
    # dataloader = Dataloader(image_folder_path, label_path)

    # tongue_color_train_loader, tongue_color_test_loader, moss_color_train_loader, moss_color_test_loader = dataloader.get_train_test_dataloader(batch_size)
    # model = LeNet5(num_types=4)
    # best_acc = 0
    # for epoch in range(num_epoch):
    #     train(model=model, train_loader=tongue_color_train_loader, lr=lr, epoch=epoch)
    #     acc = test(model=model, test_loader=tongue_color_test_loader, epoch=epoch)
    #     # if acc > best_acc:
    #     #     torch.save(model.state_dict(), '../files/LeNet_togue_color_predict.pt')
    # torch.save(model.state_dict(), '../files/LeNet_togue_color_predict.pt')
    # print(prediction(image_folder_path + '/k0500.bmp'))


    # 苔色预测
    image_folder_path = '../static/data/moss_aug'
    label_path = '../files/moss_all_features_aug.csv'
    dataloader = Dataloader(image_folder_path, label_path)

    tongue_color_train_loader, tongue_color_test_loader, moss_color_train_loader, moss_color_test_loader = dataloader.get_train_test_dataloader(batch_size)
    model = LeNet5(num_types=2)
    for epoch in range(num_epoch):
        train(model=model, train_loader=moss_color_train_loader, lr=lr, epoch=epoch)
        test(model=model, test_loader=moss_color_test_loader, epoch=epoch)
    torch.save(model.state_dict(), '../files/LeNet_moss_color_predict.pt')

    # batch_prediction(10)

