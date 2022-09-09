from multiprocessing.sharedctypes import Value
import requests
import datetime as dt
import requests


def post_request(url, payload):
    #time = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    response = requests.post(url, json=payload)
    print("status code = ", response.status_code)

    text = eval(response.text)
    return text 


def try_get_featuer(i, name, data, text):
    try:
        for j in text['runs'][i]['data']['metrics']:
            for key, value in j.items():
                if value == name:
                    data[name] =  j["value"]
        
        assert data[name] 
    except:
        data[name] = None 
        pass
    
    return data
    
def extract_info(text, features):
    """
    不同实验，设计的Loss名称不同
    loss名称需要自定义好
    """
    #loss_name = "lm loss"
    #eval_loss_name = "lm loss validation"

    data_list = []
    num_runs = len(text["runs"])
    ins = []
    time = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    
    for i in range(num_runs):
        data = {}
        
        # 添加过滤条件
        tag = text['runs'][i]['data']['tags'][0]["value"] 
        if tag in [""]:  # pass list 
            continue
        
        try:
            data["status"] = text["runs"][i]["info"]['status'] # 训练的状态
            data["experiment_id"] = text["runs"][i]["info"]["experiment_id"]
            data["tags"] = text['runs'][i]['data']['tags'][0]["value"]
            data["start_time"] = eval(str(text['runs'][i]['info']['start_time'])[:10]) # 前10位，精确到秒
        except:
            print("当前text解析失败")
            pass
        
        for feature in features:
            data = try_get_featuer(i, feature, data, text)

        try:
            data["end_time"] = eval(str(text['runs'][i]['info']['end_time'])[:10])
        except:
            data["end_time"] = 0
            pass
        
        data_list.append(data)
        
    ins = [time, data_list]

    return ins


if __name__ == '__main__':
    pass
