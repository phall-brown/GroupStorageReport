import argparse
import grp
import pwd
import subprocess
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.backends.backend_pdf import PdfPages

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
        output[mem]='secondary'
    # Primary group members
    users=pwd.getpwall()
    for user in users:
        if user.pw_gid == group.gr_gid:
            output[user.pw_name]='primary'
    return output

def get_storage(storagepath):
    """ 
    Returns storage within the specified group's directory associated
    with each.
    """
    titles=['username','parent','type',
            'GB_used','GB_avail','GB_hard','GB_grace','junk',
            'used_FL','soft_FL','hard_FL','grace_FL']
    nheader=4 # number of header lines in quota-report.txt files 
    data=pd.read_csv(storagepath,
                      sep='\s+',
                      engine='python',
                      skiprows=nheader,
                      names=titles,
                      index_col='username',
                      usecols=['username','GB_used','GB_avail'])
    total_used=data.iloc[0,0]
    total_avail=data.iloc[0,1]
    data=data.drop(data.index[0]).drop(columns='GB_avail')
    return total_used,total_avail,data

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

def make_pdf(data,outpath):
#def make_pdf(filePath):
    """
    Create plots and tables and use them to generate formatted report.
    """
#    try:
#        os.mkdir("output")
#    except OSError:
#        pass

    with PdfPages(outpath+'test.pdf') as pdf:
#    with PdfPages('output/' + filePath[:-4] + '_Analysis.pdf') as pdf:
      rcParams['font.family']='sans-serif'
      rcParams['font.sans-serif']=['Arial'] 
      
      primary=data[data.Affiliation=='primary']
      secondary=data[data.Affiliation!='primary']
      del primary['Affiliation']
      del primary['Email']
      del secondary['Affiliation']
      del secondary['Email']

      # NEED TO COMBINE PRIMARY AND SECONDARY INTO SINGLE, SORTED ARRAY TO CREATE SINGLE FORMATTED TABLE

#        df = readFile(filePath)
#        userstorage = df["Storage (GB)"]
#        userlist = df["Username"]
#        legend = buildlegendtable(df)
#        userbatchjobs = df["# Jobs (batch)"]
#        userbatchmins = pd.to_numeric(df["Core*minutes (batch)"], errors='coerce')/60.0
#        userbigmemjobs = df["# Jobs (bigmem)"]
#        userbigmemmins = pd.to_numeric(df["Core*minutes (bigmem)"], errors='coerce')/60.0
#        groupmembers = buildgroupmemberstable(df)
#        grouptotals = buildgrouptotalstable(df)

        #Create Page 1
#        fig = plt.figure(figsize=(8.27, 11.69))  # portrait orientation

#        grid_size = (100, 100)
#        def make_autopct(values):
#            def my_autopct(pct):
#                if pct==0.0:
#                    return ' '
#                elif pct < 0.1:
#                    return '<0.1'
#                else:
#                    return '{p:.1f}'.format(p=pct)
#            return my_autopct

        # Storage Share Pie Chart
#        plt.subplot2grid(grid_size, (10, 50), rowspan=25, colspan=50)
#        plt.pie(userstorage, autopct=make_autopct(userstorage), pctdistance=1.25)
#        plt.title('Storage (%)')

        # Stores list of colors for later tables, will need testing on groups with very large quantities of members
#        colorlist = plt.rcParams['axes.prop_cycle'].by_key()['color']

        # Group Member Legend w/ Color Key
#        plt.subplot2grid(grid_size, (10, 0), rowspan=25, colspan=50)
#        plt.axis('off')
#        plt.table(cellText=legend.values, cellLoc="center", cellColours=list(zip(colorlist)),
#                  colLabels=list(legend.columns), loc="center")
#        plt.title('Group Members')

        # Batch Job Share Pie Chart
#        plt.subplot2grid(grid_size, (40, 0), rowspan=25, colspan=50)
#        plt.pie(userbatchjobs, autopct=make_autopct(userbatchjobs), pctdistance=1.25)
#        plt.title('Batch: Share of Jobs (%)')

        # Batch Job Utilization Pie Chart
#        plt.subplot2grid(grid_size, (40, 50), rowspan=25, colspan=50)
#        plt.pie(userbatchmins, autopct=make_autopct(userbatchmins), pctdistance=1.25)
#        plt.title('Batch: Utilization (%)')

        # Bigmem Job Share Pie Chart
#        plt.subplot2grid(grid_size, (70, 0), rowspan=25, colspan=50)
#        plt.pie(userbigmemjobs, autopct=make_autopct(userbigmemjobs), pctdistance=1.25)
#        plt.title('Bigmem: Share of Jobs (%)')

        # Bigmem Job Utilization Pie Chart
#        plt.subplot2grid(grid_size, (70, 50), rowspan=25, colspan=50)
#        plt.pie(userbatchmins, autopct=make_autopct(userbigmemmins), pctdistance=1.25)
#        plt.title('Bigmem: Utilization (%)')

        # Page header

#        title = 'Monthly Usage Report'
#        plt.text(0.5, 0.90, title, horizontalalignment='center', verticalalignment='bottom', transform=fig.transFigure,
#                 size=24)

#        pdf.savefig()
#        plt.close()


        # Table
      fig = plt.figure(figsize=(11.69, 8.27))  # landscape orientation

      grid_size = (100, 100)

      # Primary Group Members Data Table
      plt.subplot2grid(grid_size, (10, 1), rowspan=45, colspan=99)
      plt.axis('off')
      plt.table(cellText=primary.values, cellLoc="center",
                colLabels=list(primary.columns), loc="center")
#      plt.table(cellText=secondary.values, cellLoc="center",
#                colLabels=list(primary.columns), loc="center")
#      plt.table(cellText=data.values, cellLoc="center",
#                colLabels=list(data.columns), loc="center")
      plt.title('Group Members',fontsize=20,fontweight='bold',horizontalalignment='left')

#        batch = 'Partition: Batch'
#        plt.text(0.635, 0.74, batch, verticalalignment='bottom', transform=fig.transFigure, size=8)

#        bigmem = 'Partition: Bigmem'
#        plt.text(0.8125, 0.74, bigmem, verticalalignment='bottom', transform=fig.transFigure, size=8)

        # Group Totals Data Table
      plt.subplot2grid(grid_size, (70, 0), rowspan=30, colspan=100)
      plt.axis('off')
#        plt.table(cellText=grouptotals.values, cellLoc="center", colLabels=list(grouptotals.columns), loc="center")
      plt.title('Group Totals')

      pdf.savefig()
      plt.close()

##############
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

# declarations
account={}
affiliation=[]
batch={}
bigmem={}
emailaddr={}
gpu={}
name={}
#storage={}

# constants
storagepath='/gpfs/data/ccvstaff/quota-reports/'+args.groupname+'-quota-report.txt'
outpath='/gpfs/data/ccvstaff/phall1/projects/baldrick/reports/reports.venv/GroupReport/'

# get list of group members
affiliation=get_members(args.groupname)
# get storage for group members
total_used,total_avail,storage=get_storage(storagepath)

# get general info and usage metrics for each individual user
for user in affiliation:
    name[user]=get_user_name(user)
    emailaddr[user]=get_user_email(user)
    account[user]=get_account_types(user) 
    batch[user]=get_usage(user,'batch',args.start,args.end)
    bigmem[user]=get_usage(user,'bigmem',args.start,args.end)
    gpu[user]=get_usage(user,'gpu',args.start,args.end)

# convert dicts to pandas dataframes
affiliation_df=pd.DataFrame.from_dict(affiliation,orient='index',columns=['Affiliation'])
account_df=pd.DataFrame.from_dict(account,orient='index',columns=['Account'])
name_df=pd.DataFrame.from_dict(name,orient='index',columns=['Name'])
email_df=pd.DataFrame.from_dict(emailaddr,orient='index',columns=['Email'])
batch_df=pd.DataFrame.from_dict(batch,orient='index',columns=['BatchJobs','BatchUsage'])
bigmem_df=pd.DataFrame.from_dict(bigmem,orient='index',columns=['BigmemJobs','BigmemUsage'])
gpu_df=pd.DataFrame.from_dict(gpu,orient='index',columns=['GPUJobs','GPUUsage'])

# combine dataframes into a single dataframe
data=pd.concat([name_df,email_df,affiliation_df,account_df,
               batch_df,bigmem_df,gpu_df,storage],
               axis=1,ignore_index=False) 


    
# clean up NaNs and formatting of dataframe
data['Name']=data['Name'].fillna('NA')
data['Email']=data['Email'].fillna('NA')
data['Affiliation']=data['Affiliation'].fillna('NA')
data['Account']=data['Account'].fillna('-')
data=data.fillna(0)

data['BatchJobs']=data['BatchJobs'].astype(int)
data['BatchUsage']=data['BatchUsage'].astype(int)
data['BigmemJobs']=data['BigmemJobs'].astype(int)
data['BigmemUsage']=data['BigmemUsage'].astype(int)
data['GPUJobs']=data['GPUJobs'].astype(int)
data['GPUUsage']=data['GPUUsage'].astype(int)
data['GB_used']=data['GB_used'].astype(int)

# generate output
make_pdf(data,outpath)
    
# output to screen (for debugging only)
print(data)
