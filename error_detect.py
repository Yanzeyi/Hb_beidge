import numpy as np
# from matplotlib import pyplot as plt
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn import svm
from math import ceil, floor
from outlier_dict import outlier_dict
import datetime


class detect_error(object):
    def get_accuracy(self, SLdata_list):
        pass

    def get_false_alarm(self, SLdata_list, SLMdate_list, error_index_list, month, senor_id):
        false_alarm_cnt = 0
        true_cnt = 0
        new_outlier_list = []
        # new_SLdata_list = []
        for data in outlier_dict[month][senor_id]["SLdata"]:
            new_outlier_list.append(int(data))
        for error_index in error_index_list:
            if int(SLdata_list[error_index]) in new_outlier_list:
               dict_index = new_outlier_list.index(int(SLdata_list[error_index]))
               
               if SLMdate_list[error_index].month == outlier_dict[month][senor_id]["Mdate"][dict_index].month and\
                  SLMdate_list[error_index].day == outlier_dict[month][senor_id]["Mdate"][dict_index].day:
                    true_cnt += 1
                    # print(SLdata_list[error_index], SLMdate_list[error_index])
            else:
                false_alarm_cnt += 1
        print(outlier_dict[month][senor_id]["SLdata"], outlier_dict[month][senor_id]["Mdate"])
        # return false_alarm_cnt/len(outlier_dict[month][senor_id]["SLdata"])
        return true_cnt, false_alarm_cnt, len(outlier_dict[month][senor_id]["SLdata"]) - true_cnt



def fill_point(data_list, error_index_list):
    new_list = []
    for data in data_list:
        if data_list.index(data) in error_index_list:
            if data_list.index(data) == 0:
                new_list.append(data_list[1])
            elif data_list.index(data) == len(data_list) - 1:
                new_list.append(data_list[len(data_list) - 2])
            else:
                new_list.append((data_list[data_list.index(data) - 1] + data_list[data_list.index(data) + 1])/2)
        else:
            new_list.append(data)
    return new_list

class k_means():    
    def k_choose(self ,data_list):
        SSE = []
        for k in range(1,9):
            k_tmp = KMeans(n_clusters=k)
            k_tmp.fit(np.array(data_list).reshape(-1, 1))
            SSE.append(k_tmp.inertia_) 
        return SSE
    

    def k_means_train(self, k, data_list):
        label_cnt = []
        error_index = []
        K_means_ = KMeans(n_clusters=k)
        K_means_.fit(np.array(data_list).reshape(-1, 1))
        # print(K_means_.labels_)
        data_labels = list(K_means_.labels_)
        # print(data_labels)
        # for i in range(len(data_labels)):
        #     if data_labels[i] == 1:
        #         print(i)
        for i in range(k):
            label_cnt.append(0)
        for i in range(len(data_labels)):
            label_cnt[data_labels[i]] = label_cnt[data_labels[i]] + 1
        error_label = label_cnt.index(min(label_cnt))
        if label_cnt[error_label] > label_cnt[1 - error_label] * 0.2:
            return []
        else:
            # print(label_cnt)
            error_label = label_cnt.index(min(label_cnt))
            # print(error_label)
            for i in range(len(data_labels)):
                if data_labels[i] == error_label: error_index.append(i)
            return error_index


class three_sigma():
    def __init__(self):
        pass

    def three_sigma_(self, SLdata_list, SLdata_mean, SLdata_std):
        # print(len(SLdata_list))
        if SLdata_std > SLdata_mean/10:
            error_index = []
            for i in range(len(SLdata_list)):
                if abs(SLdata_list[i] - SLdata_mean) > 1.5 * SLdata_std:
                    error_index.append(i)
        else:
            error_index = []
            for i in range(len(SLdata_list)):
                if abs(SLdata_list[i] - SLdata_mean) > 3 * SLdata_std:
                    error_index.append(i)

        return error_index
    

def return_index(func):
    def wrapper(*args, **kwargs):
        label_ = func(*args, **kwargs)
        error_index = []
        for i in range(len(label_)):
            if label_[i] == -1 : error_index.append(i)
        return error_index
    return wrapper


def return_lrweights(func):
    def wrapper(self, number):
        close_num = func(self, number)
        rn = close_num if close_num > number else close_num + 1
        rw = 1 - rn + number
        lw = 1 - rw
        return lw, rw
    return wrapper


class iostation_forest():
    @return_index
    def ioslation_forest_train(self, SLdata_list):
        isof = IsolationForest(n_estimators=100, max_samples='auto', contamination=float(0.05),max_features=1.0)
        isof.fit(np.array(SLdata_list).reshape(-1, 1))
        SLdata_label = isof.predict(np.array(SLdata_list).reshape(-1, 1))
        return SLdata_label


class box_plot():
    def box_plot_train(self, data_list):
        error_index_list = []
        sorted_list = sorted(data_list)
        num = len(sorted_list)
        q1_pos = (num + 1) / 4 - 1
        q2_pos = (num + 1) / 2 - 1
        q3_pos = 3 * (num + 1)/ 4 - 1
        q1 = self.get_q(q1_pos, sorted_list)
        q2 = self.get_q(q2_pos ,sorted_list)
        q3 = self.get_q(q3_pos ,sorted_list)
        # print(q1, q2, q3)
        IQR = q3 - q1
        bottom_line = q1 - 1.5 * IQR
        top_line = q3 + 1.5 * IQR
        for data in data_list:
            if data < bottom_line or data > top_line : error_index_list.append(data_list.index(data))
        return error_index_list
    

    def get_q(self, q_pos, data_list):

        q_lw, q_rw = self.left_or_right(q_pos)
        return q_lw * data_list[floor(q_pos)] + q_rw * data_list[ceil(q_pos)]


    @return_lrweights
    def left_or_right(self, number):
        left_diff = abs(number - ceil(number))
        right_diff = abs(floor(number) - number)
        return ceil(number) if left_diff <= right_diff else floor(number)
    
class svm_():
    @return_index
    def svm_train_(self, SLdata_list):
        clf = svm.OneClassSVM(nu=0.001, kernel="rbf", gamma=0.0001)
        clf.fit(np.array(SLdata_list).reshape(-1, 1))
        error_label = clf.predict(np.array(SLdata_list).reshape(-1, 1))
        return error_label
        # print(error_label)
        # dl.detect_error_pic(SLdata_list, error_label)

if __name__ == "__main__":
    pass
    # data_list = [13, 13.5, 13.8, 13.9, 14, 14.6, 14.8, 15, 15.2, 15.4]
    # b = box_plot()
    # b.box_plot_train(data_list)

    # data_list = [1, 3, 5 ,6 ,7 ,8, 15]
    # index_list = [0, 6]
    # print(fill_point(data_list, index_list))

    a = [1, 4, 5 ,6 ,7, 8, 9, 10]
    b = [0, 4]
    print(fill_point(a, b))
