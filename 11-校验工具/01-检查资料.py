#!/usr/bin/env python3
"""检查教材内部链接、题目结构、自测及数值。只用标准库，不改文件。"""
from pathlib import Path
import math
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []
checks = 0

def check(condition, message):
    global checks
    checks += 1
    if not condition:
        errors.append(message)

def near(actual, expected, label, tolerance=0.015):
    check(math.isclose(actual, expected, abs_tol=tolerance, rel_tol=1e-9),
          f'{label}: {actual} != {expected}')

files = sorted(ROOT.rglob('*.md'))
for path in files:
    body = path.read_text(encoding='utf-8')
    check(body.startswith('# '), f'缺少一级标题: {path.relative_to(ROOT)}')
    check(body.count('<details>') == body.count('</details>'), f'折叠标签不平衡: {path}')
    check(body.count('```') % 2 == 0, f'代码块不平衡: {path}')
    check(not re.search(r'ppgfo|gh[opusr]_[A-Za-z0-9]{15,}', body, re.I), f'不应公开的信息: {path}')
    check(not re.search(r'TODO|TBD|待补充正文|校验正在执行', body), f'尚未完成: {path}')
    for target in re.findall(r'\[[^\]\n]+\]\(([^\n)]+)\)', body):
        if re.match(r'[a-zA-Z]+:', target) or target.startswith('#'):
            continue
        target = target.split('#')[0].split(' "')[0].strip('<>')
        check((path.parent / target).is_file(), f'断开的链接: {path.relative_to(ROOT)} -> {target}')

folders = sorted(p.name for p in ROOT.iterdir() if p.is_dir() and not p.name.startswith('.'))
check([n[:2] for n in folders] == [f'{i:02}' for i in range(12)], '根目录应连续编号00至11')
core = [p for p in files if re.match(r'0[1-7]-', p.relative_to(ROOT).parts[0])]
check(len(core) == 28, f'核心讲义应28篇，实际{len(core)}')
for p in core:
    text = p.read_text()
    marker = re.search(r'^## .*?(自测|主动回忆).*$', text, re.M)
    check(marker is not None, f'缺自测: {p}')
    if marker:
        questions = text[marker.end():].split('<details>')[0]
        check(len(re.findall(r'^\d+\. ', questions, re.M)) >= 3, f'自测不足3题: {p}')
        check('<summary>' in text[marker.end():], f'缺随文解析: {p}')

question_files = sorted((ROOT / '09-练习与解析').glob('*-题目.md'))
answer_files = sorted((ROOT / '09-练习与解析').glob('*-解析.md'))
check(len(question_files) == len(answer_files) == 8, '应有8组题目和解析')
expected = {1: 15, 2: 20, 3: 10, 4: 35, 5: 20, 6: 20, 7: 40, 8: 40}
questions = {}; answers = {}
for p in question_files:
    text = p.read_text()
    check('原创学习练习，非官方试题' in text, f'原创标记缺失: {p}')
    blocks = re.split(r'^### (T\d-\d{2})\s*$', text, flags=re.M)
    for j in range(1, len(blocks), 2):
        ident, body = blocks[j], blocks[j+1]
        check(ident not in questions, f'重复题号: {ident}')
        opts = dict(re.findall(r'^([ABCD])\. (.+)$', body, re.M))
        check(set(opts) == set('ABCD'), f'不是四选项: {ident}')
        check(len(set(opts.values())) == 4, f'选项重复: {ident}')
        questions[ident] = opts
for p in answer_files:
    blocks = re.split(r'^### (T\d-\d{2})\s*$', p.read_text(), flags=re.M)
    for j in range(1, len(blocks), 2):
        ident, body = blocks[j], blocks[j+1]
        check(ident not in answers, f'重复解析: {ident}')
        key = re.search(r'\*\*答案：([ABCD])。\*\*', body)
        check(key is not None, f'缺答案: {ident}')
        why = re.findall(r'^- \*\*([ABCD])：(正确|不选)。\*\* (.+)$', body, re.M)
        check(len(why) == 4 and {x[0] for x in why} == set('ABCD'), f'未逐项解释: {ident}')
        if key:
            check([x[0] for x in why if x[1] == '正确'] == [key[1]], f'答案与解释不一致: {ident}')
            answers[ident] = key[1]
check(set(questions) == set(answers), '题目和解析题号不匹配')
for t, n in expected.items():
    check({x for x in questions if x.startswith(f'T{t}-')} == {f'T{t}-{i:02}' for i in range(1,n+1)}, f'主题{t}题数或编号错误')
check(len(questions) == 200, f'总题数应200，实际{len(questions)}')

# 以题设独立计算，再从实际正确选项中读取数值；覆盖数值选择题。
numeric = {
'T1-04':3-2, 'T1-06':(1.1*.95-1)*100, 'T1-07':(1.05/1.03-1)*100,
'T1-08':((12+30)/(10+30)-1)*100,'T1-09':.2*10+.8*(-5),
'T2-01':70,'T2-03':800/1000*100,'T2-08':100*2,'T2-09':4*10/5,
'T2-10':(4*12+8)/5,'T2-11':12-(4*12+8)/5,'T2-13':15-1,
'T4-04':(1050-50)/100,'T4-05':(10.3/10-1)*100,'T4-07':(1.2*(1-2/11)-1)*100,
'T4-09':2*20,'T4-12':100000*(1-.04*90/360),'T4-13':1000/99000*100,
'T4-14':50/950*100,'T4-15':50/1.04+1050/1.04**2,'T4-16':990+15,
'T4-17':-5*.002*100,'T4-19':(50-40)*100,'T4-20':((80000-50000)/50000-1)*100,
'T4-22':(20120-20000)*50,'T4-25':(.045-.03)*1000,'T4-26':max(103-100,0)-6,
'T4-27':max(100-80,0)-4,'T4-30':.6*100,'T4-31':.10*3,'T4-33':(110-100)-(6-2),'T4-34':(60-50)/10,
'T5-09':1000-700,'T5-12':math.ceil(12345*.001),'T5-13':100000*.0000565,
'T5-14':50000*.000042,'T5-15':(10950+100-10050)/10050*100,
'T6-01':50-30-12,'T6-02':5.6/50*100,'T6-03':5.6/18*100,'T6-04':(20-6)/10,
'T6-05':8/1,'T6-06':30/5,'T6-07':7/50*365,'T6-08':5.6/10,'T6-09':12/.56,
'T6-10':12/2,'T6-11':.4/.56*100,'T6-14':1.04/.05,'T6-16':2*12,
'T6-17':(5+6+7)/3,'T6-18':(6+7+9)/3,'T6-19':100-100/(1+2),
'T7-01':(1.25*.8-1)*100,'T7-02':(.0325-.03)*10000,'T7-03':.7*6+.3*(-4),'T7-04':.7*10,
'T7-07':600*5,'T7-08':900/1000*100,'T7-09':3*16/4,'T7-10':(2*15+9)/3,'T7-11':20-.6,
'T7-17':1040/1.04,'T7-18':60/1200*100,'T7-19':-3*(-.004)*100,
'T7-20':50000*(1-.03*120/360),'T7-21':2400/200,'T7-22':9000/30000*100,
'T7-23':(30-24)*200-100,'T7-24':30*20*2,'T7-25':max(80-70,0)-5,
'T7-26':-.5*100*2,'T7-28':30/10,'T7-31':math.ceil(100001*.001),
'T7-35':(80-48-20)/80*100,'T7-36':6/24*100,'T7-37':18/1.5,'T7-38':.6/(.1-.04),'T7-39':(8+10+12+14)/4,
'T8-01':(1.04**2-1)*100,'T8-02':(1.10/1.05-1)*100,'T8-03':(.95*1.08-1)*100,
'T8-04':((20+88)/(20+80)-1)*100,'T8-07':400*8,'T8-08':600/1000*100,
'T8-09':5*18/6,'T8-10':(3*20+12)/4,'T8-11':20-18,
'T8-17':(1030/980-1)*100,'T8-18':-6*.0025*100,'T8-19':20000*(1-.06*30/360),
'T8-20':(500-20)/40,'T8-21':(10-9.8)/10*100,'T8-22':10000/20000*100,
'T8-23':6/(1-.25),'T8-24':(2000-1980)*10*2,'T8-25':abs((.02-.025)*400),
'T8-26':max(58-50,0)-3,'T8-27':100-(4+3),
'T8-30':(21000-20200)/20200*100,'T8-31':80000*.0000565,'T8-32':200000*.000042,
'T8-35':30/100*100,'T8-36':(30-12)/15,'T8-37':.5/10*100,
'T8-38':.8*1.05/(.12-.05),'T8-39':(23-15)/(25-15)*100,
}
for ident, actual in numeric.items():
    if ident not in answers:
        check(False, f'计算校验找不到题号: {ident}')
        continue
    option = questions[ident][answers[ident]].replace('−','-')
    first = re.search(r'[-+]?\d+(?:\.\d+)?', option)
    check(first is not None, f'数值答案无数值: {ident}')
    if first:
        near(actual, float(first[0]), f'数值答案{ident}')

# 主讲义、案例表、公式表及选读工作坊的关键结果。
reference = [
('案例A资产等式',600000+400000,1000000),('案例B募资',2000000*10,20000000),
('案例B市值',10000000*12,120000000),('案例B总收益',((12-10+.4)/10)*100,24),
('红股',12*4/5,9.6),('供股',56/5,11.2),('权利价值',12-56/5,.8),
('复利三年',1000*1.05**3,1157.625),('半年复利',1000*1.03**4,1125.50881),
('有效年率',(1.03**2-1)*100,6.09),('两年年金',100/1.05+100/1.05**2,185.941),
('先涨跌',(1.2*.8-1)*100,-4),('几何平均',(math.sqrt(.96)-1)*100,-2.02041),
('年化',(1.04**6-1)*100,26.5319),('无费用组合',.8*10+.2*(-20),4),
('汇率示例',((110*7.5)/780-1)*100,5.76923),('指数价格50',100/2,50),
('债券4%',50/1.04+1050/1.04**2,1018.86095),('债券5%',50/1.05+1050/1.05**2,1000),
('债券6%',50/1.06+1050/1.06**2,981.66607),
('债券久期',(50/1.04+2*1050/1.04**2)/(50/1.04+1050/1.04**2),1.9528149),
('修正久期',(50/1.04+2*1050/1.04**2)/(50/1.04+1050/1.04**2)/1.04,1.8777066),
('追缴',50000/.7,71428.57143),('含利息权益回报',(110000-50000-4000-50000)/50000*100,12),
('二叉树',(.625*20)/1.05,11.90476),('价差净收益',10-4,6),
('交易总费用',100+100+5.65+2.7+.15+4.2,212.7),('两边费用',212.7*2,425.4),
('净利率',5.6/50*100,11.2),('ROA',5.6/38*100,14.73684),
('ROE',5.6/18*100,31.11111),('存货天数',365/6,60.83333),('收款天数',7/50*365,51.1),
('留存比例',(1-.4/.56)*100,28.57143),('股息模型',.4*1.03/(.08-.03),8.24),
('两阶段估值',.44/1.08+(.484+.484*1.03/.05)/1.08**2,9.37037),
('五日均线',57/5,11.4),('滚动均线',61/5,12.2),
('分散波动',math.sqrt(.25*.04+.25*.09)*100,18.02776),
('简化可持续增长',(1-.4/.56)*(5.6/18)*100,8.88889),
('年复利平价',100+6-100/1.05,10.76190),
]
for label, actual, expected_value in reference:
    near(actual, expected_value, label)
N = lambda x: (1 + math.erf(x/math.sqrt(2))) / 2
call = 100*N(.35) - 100*math.exp(-.05)*N(.15)
near(call, 10.4506, 'Black-Scholes认购')
near(call+100*math.exp(-.05)-100, 5.5735, 'Black-Scholes认沽')
# 同一正确选项包含多个数值的额外核对。
near(100+4+3, 107, '模拟B跨式上打平')
near(8/100*100, 8, '模拟B净利率')
near(.5/1*100, 50, '模拟B派息率')

han_count = sum(len(re.findall(r'[\u3400-\u9fff]', p.read_text())) for p in files)
print(f'Markdown文件: {len(files)}；核心讲义: {len(core)}；选择题: {len(questions)}；中文字: {han_count}')
print(f'结构及数值断言: {checks}；数值选择题独立复算: {len(numeric)}；主线计算: {len(reference)+5}')
if errors:
    for item in errors:
        print('错误:', item)
    sys.exit(1)
print('检查通过：内部文件链接、编号、自测、题目解析及所列计算均符合检查条件。')
