import pandas as pd

def pd_data_distribute(pd_data, key, num_bins=10):
    '''
    获取dataframe表格某一列的统计信息
    :param pd_data: dataframe表格
    :param key: 列名
    :param num_bins: 区间数量
    :return: {'bins': , 'num': }
    '''

    min_value = pd_data[key].min()
    max_value = pd_data[key].max()
    gap = (max_value - min_value) / num_bins
    if gap >=7:
        gap = int(round(gap / 10) * 10)     # 区间大小
    elif gap >=3:
        gap = 5
    else:
        gap = 1
    lower_bound = int(min_value / gap) * gap
    upper_bound = (int(max_value / gap) + 1) * gap
    bins = list(range(lower_bound, upper_bound + gap, gap))
    cut = pd.cut(pd_data[key], bins=bins, right=False, include_lowest=True)
    pd_distribute = pd_data[key].groupby(cut).count()
    distribute = {'bins': bins, 'num': pd_distribute.values.tolist()}
    return distribute


def get_statistic_info(pd_patient_info):
    num_patient = len(pd_patient_info)  # 病人个数
    num_male = len(pd_patient_info[pd_patient_info['sex'] == '1'])  # 男性个数
    num_female = len(pd_patient_info[pd_patient_info['sex'] == '2'])  # 女性个数

    num_pos = len(pd_patient_info[pd_patient_info['symptoms_type'] == '1'])  # 肾阳虚个数
    num_neg = len(pd_patient_info[pd_patient_info['symptoms_type'] == '2'])  # 肾阴虚个数

    # 年龄段统计
    age_distribute = pd_data_distribute(pd_patient_info, 'age', num_bins=10)
    # print('age_distribute: ', age_distribute)
    # age_distribute = {}
    # for i in range(10):
    #     min_age = 10 * i
    #     max_age = 10 * (i + 1)
    #     tmp = pd_patient_info[pd_patient_info['age'] >= min_age]
    #     num = len(tmp[tmp['age'] < max_age])
    #     age_range = str(min_age) + '-' + str(max_age)
    #     age_distribute.update({age_range: num})

    # 血肌酐值统计
    sc_distribute = pd_data_distribute(pd_patient_info, 'serum_creatinine', num_bins=10)
    # print('sc_distribute: ', sc_distribute)

    # eGFR值统计
    eGFR_distribute = pd_data_distribute(pd_patient_info, 'eGFR', num_bins=10)
    # print('eGFR_distribute: ', eGFR_distribute)

    # 所有要传给前端的数据
    data = {
        'num_patient': num_patient,  # 病人个数
        'num_male': num_male,  # 男性个数
        'num_female': num_female,  # 女性个数
        'num_pos': num_pos,  # 肾阳虚病人个数
        'num_neg': num_neg,  # 肾阴虚病人个数
        'age_distribute': age_distribute,  # 年龄段分布
        'sc_distribute': sc_distribute,  # 血肌酐值分布
        'eGFR_distribute': eGFR_distribute,  # eGFR值分布
    }
    return data
