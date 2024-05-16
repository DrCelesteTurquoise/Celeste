from sikulix4python import *
import py4j

# cmd java -jar C:\NFTT\BTC\Test/sikulixide-2.0.5.jar -p
import glob

time.sleep(6)
 
addImagePath(r'C:\NFTT\BTC\Test\pic')  #括号内应该填入图像所在文件夹
scr=Screen()
 
file_out_dir = r'C:\NFTT\BTC\Test\pic\\'
id_file = file_out_dir + '*.png'
 
#几个文件
len_file = len(glob.glob(id_file))
# print(len_file)
#遍历文件路径
# print(glob.glob(id_file))
 
 
for img in glob.glob(id_file):
    print(img)
 
    #match = scr.exists(img, 3.) # method missing, wrong signature
    match = scr.exists(img, 3.0) # number must be float/double
    if match:
        #match.highlight(2)
        match.click()  #模拟鼠标单击
        # match.type(img,"lilili\n\n")  #模拟定位并输入文本，默认是英文
 