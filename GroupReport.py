import argparse
import grp
import pwd
#import matplotlib
import subprocess

# DEFINE FUNCTIONS
def get_members(groupname):
    """
    Returns a dict of (username,affiliation) for all members of the
    specified Linux group.
    affiliation=1 ==> group is user's primary group
    affiliation=2 ==> group is a secondary group for user
    """
    output={}
    
    # Secondary group members
    group=grp.getgrnam(groupname)
    for mem in group.gr_mem:
        output[mem]=2
    # Primary group members
    users=pwd.getpwall()
    for user in users:
        if user.pw_gid == group.gr_gid:
            output[user.pw_name]=1
    return output

def get_user_name(username):
    """
    Returns user's name
    """
    tmp=[]

    try: 
      tmp=pwd.getpwnam(username)
      try:
        output=tmp.pw_gecos.split(',')[0]
      except:
        output='NA'
    except:
      output='NA'

    return output

def get_user_email(username):
    """ 
    Returns user's email address
    """
    tmp=[]
 
    try:
      tmp=pwd.getpwnam(username)
      try:
        output=tmp.pw_gecos.split(',')[4]
      except:
        output='NA'
    except:
      output='NA'

    return output

def get_account_types(username):
    """
    Returns a list of current account types associated with the specified user.
    """
    output=[]
    # Define premium account types (based on Linux groups)
    # Priority accounts
    priority=['priority','priority1','priority2','priority3','priority4',
             'priority5','priority6','priority7','priority8','priority9']
    priorityp=['priority+','priority+1']
    # Premium GPU accounts
    prigpu=['pri-gpu','pri-gpu1']
    prigpup=['pri-gpu+','pri-gpu+1']
    gpuhe=['gpu-he','gpu-he1']
    # Bigmem accounts
    # NEED TO ADD WHEN ADDED TO OSCAR
   
    # Get list of all groups to which user belongs
    proc=subprocess.Popen(['id','-Gn',username],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding='utf-8')
    out,err=proc.communicate()
    groups=list(out.strip('\n').split(" ")) 
    
    # Determine if user belongs to any groups associated with premium accounts 
    for group in priority:
      if group in groups:
        output.append('priority')
    for group in priorityp:
      if group in groups:
        output.append('priority+')
    for group in prigpu:
      if group in groups:
        output.append('pri-gpu')
    for group in prigpup:
      if group in groups:
        output.append('pri-gpu+')
    for group in gpuhe:
      if group in groups:
        output.append('gpu-he')

    return output

def get_usage(username,partition,start,end):
    """
    Returns total usage (i.e., jobs run) on the specified partition
    for the given user over the period in question.
    """
    output=[]
    # Get summary of jobs (# of jobs, total time) on given partition
    proc=subprocess.Popen(['/usr/local/bin/sacct',
                          '-u',username,
                          '-S',start,
                          '-E',end,
                          '-r',partition,
                          '-X','-n','--format=CPUTimeRaw'],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           encoding='utf-8')
    out,err=proc.communicate()
    times=list(out.splitlines())
    times=[int(i) for i in times]

    # output[0]: total number of jobs
    # output[1]: total CPUTime of jobs (in units of cpu•s) 
    output=[len(times),sum(times)]
    return output

def get_storage(storagepath):
    """
    Returns storage within the specified group's directory associated
    with each.
    """
    output={}
 
    file=open(storagepath)

    file.close()

# MAIN PROGRAM
# get input options
parser=argparse.ArgumentParser(description=
    'Generate Oscar resource usage report for a particular group.')
parser.add_argument('groupname',
                    help='Name of group to create report for.',
                    type=str)
parser.add_argument('-S',
                    dest='start',
                    help='Beginning of report period, formatted as YYYY-MM-DD.',
                    type=str)
parser.add_argument('-E',
                    dest='end',
                    help='End of report period, formatted as YYYY-MM-DD.',
                    type=str)

args=parser.parse_args()                    

account={}
affiliation=[]
batch={}
bigmem={}
emailaddr={}
gpu={}
name={}
storage={}

# constants
storagepath='/gpfs/data/ccvstaff/quota-reports/'+args.groupname+'-quota-report.txt'

# get list of group members
affiliation=get_members(args.groupname)
#storage=get_storage(args.groupname)

# get usage and storage info for each individual user
for user in affiliation:
    name[user]=get_user_name(user)
    emailaddr[user]=get_user_email(user)
    account[user]=get_account_types(user) 
    batch[user]=get_usage(user,'batch',args.start,args.end)
    bigmem[user]=get_usage(user,'bigmem',args.start,args.end)
    gpu[user]=get_usage(user,'gpu',args.start,args.end)
    
    
# output to screen (for debugging only)
print(args.groupname)
print(args.start)
print(args.end)
print(account)
print(name)
print(emailaddr)
print(affiliation)
print(batch)
print(bigmem)
print(gpu)

