from pylab import *
def getint():
    a=raw_input()
    isint=False
    while (not isint):
        a=raw_input()
        try:
            a=int(a)
            isint=True
        except:
            pass
    return a
#First read in data:
#First line is the startnum
i=getint()
num=800
x=zeros(2*num)
y=zeros(2*num)
total=0
y[0]=i
y[1]=i
x[0]=0
i=abs(i-1)
for p in xrange(1,len(y)/2):
    y[2*p]=i
    y[2*p+1]=i
    i=abs(i-1)
    total += getint()
    x[2*p-1]=total
    x[2*p]=total
x[len(x)-1]=total+getint()
plot(x,y)
ylim((-1,2))
show()
