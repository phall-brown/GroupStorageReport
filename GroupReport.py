import argparse
import grp
import pwd
import subprocess
import numpy as np
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
            'StorageGB','GB_avail','GB_hard','GB_grace','junk',
            'used_FL','soft_FL','hard_FL','grace_FL']
    nheader=4 # number of header lines in quota-report.txt files 
    data=pd.read_csv(storagepath,
                      sep='\s+',
                      engine='python',
                      skiprows=nheader,
                      names=titles,
                      index_col='username',
                      usecols=['username','StorageGB','GB_avail'])
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
    pribigmem=['pri-bigmem','pri-bigmem1']
 
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
    for group in pribigmem:
      if group in groups:
        output.append('pri-bigmem')

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
    # output[1]: total CPUTime of jobs (in units of cpu•hr) 
    output=[len(times),sum(times)/3600]
    return output

def make_pdf(data,allocation,args,outpath):
    """
    Create plots and tables and use them to generate formatted report.
    """
    with PdfPages(outpath+args.groupname+'_test.pdf') as pdf:
      rcParams['font.family']='sans-serif'
#      rcParams['font.sans-serif']=['Arial'] 

      # Create Page 1 - Summary Table and Storage
      fig = plt.figure(figsize=(7.5, 10))  # portrait orientation
      grid_size=(20,3)

      # Text headings and annotations
      # Report Header
      ax1=plt.subplot2grid(grid_size,(0,0),rowspan=2,colspan=3)
      plt.axis('off')
      plt.text(0.5,1.0,
               'Oscar Monthly Usage Report',
               horizontalalignment='center',
               verticalalignment='bottom',
               transform=ax1.transAxes,
               size=14,
               fontweight='bold')
      plt.text(0.5,0.75,
               'Group: '+args.groupname,
               horizontalalignment='center',
               verticalalignment='top',
               transform=ax1.transAxes,
               size=10,
               fontweight='bold')
      plt.text(0.5,0.5,
               args.start+' to '+args.end,
               horizontalalignment='center',
               verticalalignment='top',
               transform=ax1.transAxes,
               size=10,
               fontweight='bold')

      # 1. Summary
      # get formatted data
      members_summary,storage_summary,accounts_summary=format_summary(data,allocation)
      # heading
      ax3=plt.subplot2grid(grid_size,(2,0),rowspan=2,colspan=3)
      plt.axis('off')
      plt.text(-0.1,0.75,
               '1. Summary',
               horizontalalignment='left',
               verticalalignment='center',
               size=12,
               fontweight='bold')
      # content
      ax4=plt.subplot2grid(grid_size,(4,0),rowspan=6,colspan=1)
      table4=plt.table(cellText=members_summary,cellLoc='left',
                loc='upper center')
      table4.auto_set_font_size(False)
      table4.set_fontsize(9)
      table4.auto_set_column_width([0,1])
      table4.scale(1,2)
      plt.title('Group Members',size=10,fontweight='bold')
      plt.axis('off')

      ax5=plt.subplot2grid(grid_size,(4,1),rowspan=6,colspan=1)
      table5=plt.table(cellText=accounts_summary,cellLoc='left',
                loc='upper center')
      table5.auto_set_font_size(False)
      table5.set_fontsize(9)
      table5.auto_set_column_width([0,1])
      table5.scale(1,2)
      plt.title('Premium Accounts',size=10,fontweight='bold')
      plt.axis('off')

      ax6=plt.subplot2grid(grid_size,(4,2),rowspan=6,colspan=1)
      table6=plt.table(cellText=storage_summary,cellLoc='right',
                loc='upper center')
      table6.auto_set_font_size(False)
      table6.set_fontsize(9)
      table6.auto_set_column_width([0,1])
      table6.scale(1,2)
      plt.title('Storage (GB)',size=10,fontweight='bold')
      plt.axis('off')

      # 2. Storage - Heading
      ax7=plt.subplot2grid(grid_size,(10,0),rowspan=1,colspan=3)
      plt.axis('off')
      plt.text(-0.1,0,
               '2. Storage (total allocation: '+str(allocation)+' GB)',
               horizontalalignment='left',
               verticalalignment='bottom',
               size=12,
               fontweight='bold')

      # 2. Storage - Bar Chart
      ax8=plt.subplot2grid(grid_size,(12,0),rowspan=9,colspan=3)
      storage,labels=format_storage(data,allocation)

      y_offset=0        # initialize vertical-offset for the stacked bars
      n_rows=len(storage)
      for row in range(n_rows):
        ax8.bar(0.5,storage,
                0.2,bottom=y_offset)
        y_text=y_offset+(0.5*storage[row])
        y_offset=y_offset+storage[row]
        ax8.text(0.5,y_text,
                 labels[row],
                 horizontalalignment='center',
                 verticalalignment='center',
                 size=9,
                 color='white')

      ax8.text(0.02,0,
               '0 GB',
               horizontalalignment='right',
               verticalalignment='bottom',
               transform=ax8.transAxes,
               size=10,
               color='black')

      ax8.text(0.02,1,
               str(allocation)+' GB',
               horizontalalignment='right',
               verticalalignment='top',
               transform=ax8.transAxes,
               size=10,
               color='black')

#      title='Total Allocation: '+str(allocation)+' GB'
#      plt.title(title,size=10,fontweight='bold')
      plt.axis('off')

      pdf.savefig()
      plt.close()

      # Create page 2 - Usage
      fig=plt.figure(figsize=(7.5,10))  # portrait orientation
      grid_size=(20,1)

      # Text headings and annotations
      # 3. Usage - Heading
      ax1=plt.subplot2grid(grid_size,(0,0),rowspan=1,colspan=1)
      plt.axis('off')
      ax1.text(-0.1,1,
               '3. Usage',
               horizontalalignment='left',
               verticalalignment='bottom',
               transform=ax1.transAxes,
               size=12,
               fontweight='bold')
      # Batch
      ax2=plt.subplot2grid(grid_size,(1,0),rowspan=4,colspan=1)
      usage,jobs,labels=format_usage(data,'BatchUsage','BatchJobs')
      x=np.arange(len(usage))
      w=0.33    # width of bars in plot
      plt.xticks(x,labels,fontsize=10,rotation=45)
      uplot=ax2.bar(x-w/2,usage,width=w,color='b')
#      uplot=ax2.bar(x-w/2,usage/3600,width=w,color='b')
      plt.ylabel('Usage (core•hrs)',weight='bold')
      ax3=ax2.twinx()
      nplot=ax3.bar(x+w/2,jobs,width=w,color='g')
      plt.ylabel('Jobs (#)',weight='bold')
      plt.legend([uplot,nplot],['Usage (core•hrs)','Jobs (#)'])
      plt.title('Batch Partition',size=11,weight='bold')
      if jobs.gt(0).sum()==0:
        ax2.set_yticks([])
        ax3.set_yticks([])
        ax3.text(0.5,0.5,
                 'No jobs during this period',
                 horizontalalignment='center',
                 verticalalignment='center',
                 transform=ax3.transAxes,
                 size=11,
                 fontweight='bold')
      # GPU
      ax4=plt.subplot2grid(grid_size,(8,0),rowspan=4,colspan=1)
      usage,jobs,labels=format_usage(data,'GPUUsage','GPUJobs')
      x=np.arange(len(usage))
      w=0.33    # width of bars in plot
      plt.xticks(x,labels,fontsize=10,rotation=45)
      uplot=ax4.bar(x-w/2,usage,width=w,color='b')
#      uplot=ax4.bar(x-w/2,usage/3600,width=w,color='b')
      plt.ylabel('Usage (core•hrs)',weight='bold')
      ax5=ax4.twinx()
      nplot=ax5.bar(x+w/2,jobs,width=w,color='g')
      plt.ylabel('Jobs (#)',weight='bold')
      plt.legend([uplot,nplot],['Usage (core•hrs)','Jobs (#)'])
      plt.title('GPU Partition',size=11,weight='bold')
      if jobs.gt(0).sum()==0:
        ax4.set_yticks([])
        ax5.set_yticks([])
        ax5.text(0.5,0.5,
                 'No jobs during this period',
                 horizontalalignment='center',
                 verticalalignment='center',
                 transform=ax5.transAxes,
                 size=11,
                 fontweight='bold')
      # Bigmem
      ax6=plt.subplot2grid(grid_size,(15,0),rowspan=4,colspan=1)
      usage,jobs,labels=format_usage(data,'BigmemUsage','BigmemJobs')
      x=np.arange(len(usage))
      w=0.33    # width of bars in plot
      plt.xticks(x,labels,fontsize=10,rotation=45)
      uplot=ax6.bar(x-w/2,usage,width=w,color='b')
#      uplot=ax6.bar(x-w/2,usage/3600,width=w,color='b')
      plt.ylabel('Usage (core•hrs)',weight='bold')
      ax7=ax6.twinx()
      nplot=ax7.bar(x+w/2,jobs,width=w,color='g')
      plt.ylabel('Jobs (#)',weight='bold')
      plt.legend([uplot,nplot],['Usage (core•hrs)','Jobs (#)'])
      plt.title('Large Memory Partition',size=11,weight='bold')
      if jobs.gt(0).sum()==0:
        ax6.set_yticks([])
        ax7.set_yticks([])
        ax7.text(0.5,0.5,
                 'No jobs during this period',
                 horizontalalignment='center',
                 verticalalignment='center',
                 transform=ax7.transAxes,
                 size=11,
                 fontweight='bold')

      # Save figures
      pdf.savefig()
      plt.close()

      # Creat page 3 - Members
      # Table
      dataf=format_members(data)
      n_max=25 # maximum number of table entries that can fit on one page
      if len(dataf)>n_max:
        n_iter=0
        while n_iter>=0:
          n_iter=n_iter+1
          i_start=int((n_iter-1)*n_max)
          i_end=int((n_iter*n_max)-1)
          if i_end>=len(dataf):  # check to see if final section of table
            i_end=len(dataf)-1
            n_iter=-1            # condition for leaving loop
          dataf_tmp=dataf.iloc[i_start:i_end]

          fig=plt.figure(figsize=(10,7.5))  # landscape orientation
          ax=fig.add_subplot(1,1,1)
          plt.text(-0.1,1,
               '4. Group Members',
               horizontalalignment='left',
               verticalalignment='bottom',
               transform=ax.transAxes,
               size=12,
               fontweight='bold')
          table=ax.table(cellText=dataf_tmp.values,cellLoc='left',
                      colLabels=dataf_tmp.columns,
                      loc='upper center')
          table.auto_set_font_size(False)
          table.set_fontsize(8)
          table.auto_set_column_width([0,1,2,3,4,5,6,7,8,9])
          table.scale(1,1.1)
          ax.axis('off')
          pdf.savefig()
          plt.close()

      else:
        fig=plt.figure(figsize=(10,7.5))  # landscape orientation
        ax=fig.add_subplot(1,1,1)
        plt.text(-0.1,1,
             '4. Group Members',
             horizontalalignment='left',
             verticalalignment='bottom',
             transform=ax.transAxes,
             size=12,
             fontweight='bold')
        table=ax.table(cellText=dataf.values,cellLoc='left',
                    colLabels=dataf.columns,
                    loc='upper center')
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.auto_set_column_width([0,1,2,3,4,5,6,7,8,9])
        table.scale(1,1.1)
        ax.axis('off')
        pdf.savefig()
        plt.close()

def format_summary(data,allocation):
     # Group members
     n_members=len(data)
     n_primary=len(data[data.Affiliation=='primary'])
     n_secondary=n_members-n_primary
     # Storage 
     used=data['StorageGB'].sum()
     avail=allocation-used
     # Accounts 
     # consider only primary accounts
     datap=data[data.Affiliation=='primary']
     n_priority=len(datap[datap.Account=='priority'])
     n_priorityp=len(datap[datap.Account=='priority+'])
     n_prigpu=len(datap[datap.Account=='pri-gpu'])
     n_prigpup=len(datap[datap.Account=='pri-gpu+'])
     n_gpuhe=len(datap[datap.Account=='gpu-he'])
     n_pribigmem=len(datap[datap.Account=='pri-bigmem'])
     # Prepare formatted output for tables
     out_members=[['Primary',n_primary],
                  ['Secondary',n_secondary],
                  ['Total',n_members]]
     out_storage=[['Allocation',allocation],
                  ['Used',used],
                  ['Available',avail]]
     out_accounts=[['Priority',n_priority],
                   ['Priority+',n_priorityp],
                   ['Standard GPU Priority',n_prigpu],
                   ['Standard GPU Priority+',n_prigpup],
                   ['High-End GPU Priority',n_gpuhe],
                   ['Large Memory Priority',n_pribigmem]]

     return out_members,out_storage,out_accounts

def format_storage(data,allocation):
     # sort data based on storage
     data.sort_values(by=['StorageGB'],ascending=False,ignore_index=True,inplace=True)
     # eliminate instances where storage = 0
     data=data[data['StorageGB']>0]
     # find number of users (rows) with non-zero storage
     n_users=len(data)
     # limit output to n_max users
     n_max=5
     if n_users>n_max:
       out_values=data['StorageGB'].iloc[:n_max]
       out_labels=data['Username'].iloc[:n_max]
       for i in range(0,n_max):
         out_labels[i]=out_labels[i]+': '+str(data['StorageGB'].iloc[i])+' GB'
       out_values[n_max]=data['StorageGB'].iloc[n_max:].sum()
       out_labels[n_max]='All Others'+': '+str(data['StorageGB'].iloc[:n_max].sum())+' GB'
     else:
       out_values=data['StorageGB'].iloc[:n_users]
       out_labels=data['Username'].iloc[:n_users]
     # insert entry to account for unused storage space
     # at beginning of series for plotting purposes
       for i in range(0,n_users):
         out_labels[i]=out_labels[i]+': '+str(data['StorageGB'].iloc[i])+' GB'
     n_rows=len(out_values)
     out_values[n_rows]=allocation-data['StorageGB'].sum()
     out_labels[n_rows]='Available'+': '+str(allocation-data['StorageGB'].sum())+' GB'
     return out_values,out_labels

def format_usage(data,label_usage,label_jobs):
     # sort data based on usage
     data.sort_values(by=[label_usage],ascending=False,ignore_index=True,inplace=True)
     # consider users with primary group affiliation only
     data=data[data.Affiliation=='primary']
     # find number of users (rows)
     n_users=len(data)
     n_max=10           # maximum # of users to include in plot
     if n_users>n_max:
       out_usage=data[label_usage].iloc[:n_max]
       out_jobs=data[label_jobs].iloc[:n_max]
       out_labels=data['Username'].iloc[:n_max]
       out_usage[n_max]=data[label_usage].iloc[n_max:].sum()
       out_jobs[n_max]=data[label_jobs].iloc[n_max:].sum()
       out_labels[n_max]='All Others'
     else:
       out_usage=data[label_usage].iloc[:n_users]
       out_jobs=data[label_jobs].iloc[:n_users]
       out_labels=data['Username'].iloc[:n_users]
     return out_usage,out_jobs,out_labels

def format_members(data):
      # format data array
      # remove unneeded columns
      del data['Email']
      # create sub-dataframes based on affiliation (for subsequent formatting)
      primary=data[data.Affiliation=='primary']
      secondary=data[data.Affiliation=='secondary']
      other=data[data.Affiliation=='NA']
      # create header line to separate table entries by affiliation
      heading=pd.DataFrame({'Username':'','Name':'','Account':'',
                            'BatchJobs':'','BatchUsage':'',
                            'BigmemJobs':'','BigmemUsage':'',
                            'GPUJobs':'','GPUUsage':'',
                            'StorageGB':''},index=[0])
      # sort alphabetically by username and concatenate to create single dataframe,
      # accounting for possibility of affiliations with no members
      if len(primary)>0:
        primary=primary.sort_values(by=['Username'],ascending=True,ignore_index=True)
        del primary['Affiliation']
        heading['Username']='PRIMARY'
        primary=pd.concat([heading,primary]).reset_index(drop=True)
        output=primary
      if len(secondary)>0:
        secondary=secondary.sort_values(by=['Username'],ascending=True,ignore_index=True)
        del secondary['Affiliation']
        heading['Username']='SECONDARY'
        secondary=pd.concat([heading,secondary]).reset_index(drop=True)
        if len(primary)>0:
          output=pd.concat([output,secondary]).reset_index(drop=True)
        else:
          output=secondary
      if len(other)>0:
        other=other.sort_values(by=['Username'],ascending=True,ignore_index=True)
        del other['Affiliation']
        heading['Username']='OTHER'
        other=pd.concat([heading,other]).reset_index(drop=True)
        if (len(primary)>0 or len(secondary)>0):
          output=pd.concat([output,other]).reset_index(drop=True)
        else:
          output=other
      # set column headings for use in final report
      output.columns=['Username', 'Name', 'Account', 'Batch (n)',
              'Batch (core•hr)', 'Mem (n)', 'Mem (core•hr)', 'GPU (n)',
              'GPU (core•hr)','Storage (GB)']

      return output

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

# constants
storagepath='/gpfs/data/ccvstaff/quota-reports/'+args.groupname+'-quota-report.txt'
outpath='/gpfs/data/ccvstaff/phall1/projects/baldrick/reports/reports2.venv/output/'

# get list of group members
affiliation=get_members(args.groupname)
# get storage for group members
total_used,allocation,storage=get_storage(storagepath)

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
               axis=1,ignore_index=False).reset_index(drop=False) 
data.rename(columns={'index':'Username'},inplace=True)

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
data['StorageGB']=data['StorageGB'].astype(int)

#print(data)
#print(data.columns)
# generate output
make_pdf(data,allocation,args,outpath)
