import re

str_raw = '[CQ:image,file=https://xxxx/xxxx/xxx&amp;rkey=ssss,summary=&#91;图片&#93;,subType=11]'
print(str_raw)
cq_list = re.findall(r'(\[CQ:(\S+?),(\S+?)])', str_raw)
print(cq_list)
