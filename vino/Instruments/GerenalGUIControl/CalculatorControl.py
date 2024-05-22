from TDaiGUIControl import *

# cmd java -jar C:\NFTT\QSTSP\stable/sikulixide-2.0.5.jar -p
import glob
 
addImagePath(r'C:\NFTT\BTC\Test\pic4Calculator')
scr=Screen()
 
file_out_dir = r'C:\NFTT\BTC\Test\pic4Calculator\\'
id_file = file_out_dir + '*.png'
 
for img in glob.glob(id_file):
    print(img)
 
    match = scr.exists(img, 3.0)
    if match:
        # match.highlight()
        match.click()  #模拟鼠标单击
        # match.type(img,"lilili\n\n")  #模拟定位并输入文本，默认是英文
 