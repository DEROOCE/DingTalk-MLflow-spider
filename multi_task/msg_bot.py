import urllib
import json
import urllib.response
import urllib.request
import urllib.parse

# 自定义机器人的封装类
class DtalkRobot(object):
    """docstring for DtRobot"""
    webhook = ""

    def __init__(self, webhook):
        super(DtalkRobot, self).__init__()
        self.webhook = webhook

    # text类型
    def sendText(self, msg, isAtAll=False, atMobiles=[]):
        data = {"msgtype": "text", "text": {"content": msg}, "at": {"atMobiles": atMobiles, "isAtAll": isAtAll}}
        return self.post(data)

    # markdown类型
    def sendMarkdown(self, title, text):
        data = {"msgtype": "markdown", "markdown": {"title": title, "text": text}}
        return self.post(data)

    # link类型
    def sendLink(self, title, text, messageUrl, picUrl=""):
        data = {"msgtype": "link", "link": {"text": text, "title": title, "picUrl": picUrl, "messageUrl": messageUrl}}
        return self.post(data)

    # ActionCard类型
    def sendActionCard(self, actionCard):
        data = actionCard.getData();
        return self.post(data)

    # FeedCard类型
    def sendFeedCard(self, links):
        data = {"feedCard": {"links": links}, "msgtype": "feedCard"}
        return self.post(data)

    def post(self, data):
        # post_data = json.JSONEncoder().encode(data)
        #print(data)
        post_data = json.dumps(data).encode()
        req = urllib.request.Request(self.webhook, post_data)
        req.add_header('Content-Type', 'application/json')
        content = urllib.request.urlopen(req).read()
        print(content)
        return content


# ActionCard类型消息结构
class ActionCard(object):
    """docstring for ActionCard"""
    title = ""
    text = ""
    singleTitle = ""
    singleURL = ""
    btnOrientation = 0
    hideAvatar = 0
    btns = []

    def __init__(self, arg=""):
        super(ActionCard, self).__init__()
        self.arg = arg

    def putBtn(self, title, actionURL):
        self.btns.append({"title": title, "actionURL": actionURL})

    def getData(self):
        data = {"actionCard": {"title": self.title, "text": self.text, "hideAvatar": self.hideAvatar,
                               "btnOrientation": self.btnOrientation, "singleTitle": self.singleTitle,
                               "singleURL": self.singleURL, "btns": self.btns}, "msgtype": "actionCard"}
        return data


# FeedCard类型消息格式
class FeedLink(object):
    """docstring for FeedLink"""
    title = ""
    picUrl = ""
    messageUrl = ""

    def __init__(self, arg=""):
        super(FeedLink, self).__init__()
        self.arg = arg

    def getData(self):
        data = {"title": self.title, "picURL": self.picUrl, "messageURL": self.messageUrl}
        return data

if __name__ == "__main__":
    pass
