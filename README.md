# GroupReport
Generate a summary resource usage report for a given Oscar user group over a fixed period of time. The script generates a report in the form of a PDF that can be sent to the owner or designated representative for the group via email to aid them in managing the groups' use of Oscar. The report contains the following sections:
1. Summary
2. Storage
3. Usage
4. Group members

# Basic Usage
`python groupreport.py groupname -S yyyy-mm-dd -E yyyy-mm-dd`

`groupname` name of a Linux group on Oscar

`-S` start date of period over which to report usage

`-E` end date of period over which to report usage

#
