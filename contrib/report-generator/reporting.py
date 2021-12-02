#!/usr/bin/python3

import sys
import json
import pandas as pd
from io import BytesIO

this = sys.modules[__name__]


def bigiqXLS(jsonfile,outputfile):
  with open(jsonfile) as f:
    iJson = json.load(f)

  print("-- Importing JSON")
  f5AllDetails = pd.DataFrame(iJson['details'])

  print("-- Analyzing CVE")
  f5AllCVE = pd.DataFrame()
  for cveArray in f5AllDetails['CVE']:
    for cve in cveArray[0]:
      cveInfo=cveArray[0][cve]
      f5AllCVE=f5AllCVE.append(cveInfo,ignore_index=True)

  f5AllCVESummary=f5AllCVE.drop_duplicates()

  f5allCVECritical=f5AllCVESummary[f5AllCVESummary['baseSeverity'] == 'CRITICAL'].sort_values(by=['baseScore','exploitabilityScore'],ascending=False)
  f5allCVECritical = f5allCVECritical[['id', 'url', 'baseSeverity', 'baseScore', 'exploitabilityScore', 'description']]
  f5allCVEHigh=f5AllCVESummary[f5AllCVESummary['baseSeverity'] == 'HIGH'].sort_values(by=['baseScore','exploitabilityScore'],ascending=False)
  f5allCVEHigh = f5allCVEHigh[['id', 'url', 'baseSeverity', 'baseScore', 'exploitabilityScore', 'description']]
  f5allCVEMedium=f5AllCVESummary[f5AllCVESummary['baseSeverity'] == 'MEDIUM'].sort_values(by=['baseScore','exploitabilityScore'],ascending=False)
  f5allCVEMedium = f5allCVEMedium[['id', 'url', 'baseSeverity', 'baseScore', 'exploitabilityScore', 'description']]
  f5allCVELow=f5AllCVESummary[f5AllCVESummary['baseSeverity'] == 'LOW'].sort_values(by=['baseScore','exploitabilityScore'],ascending=False)
  f5allCVELow = f5allCVELow[['id', 'url', 'baseSeverity', 'baseScore', 'exploitabilityScore', 'description']]

  print("-- Analyzing TMOS releases")
  allVersionSummary=pd.DataFrame(f5AllDetails.groupby(['version'])['hostname'].count()).rename(columns={'hostname':'count'})

  print("-- Analyzing hardware devices")
  f5Hardware = f5AllDetails[f5AllDetails['isVirtual'] == 'False'].filter(['hostname','platformMarketingName'])
  f5Hardware = pd.DataFrame(f5Hardware.groupby(['platformMarketingName'])['hostname'].count()).rename(columns={'hostname':'count'})

  print("-- Analyzing Virtual Editions")
  f5VE = f5AllDetails[f5AllDetails['isVirtual'] == 'True']

  print("All devices:",f5AllDetails.shape[0])
  print("- Hardware :",f5Hardware.shape[0])
  print("- VE & vCMP:",f5VE.shape[0])
  print("All CVE    :",f5AllCVE.shape[0])
  print("- Critical :",f5allCVECritical.shape[0])
  print("- High     :",f5allCVEHigh.shape[0])
  print("- Medium   :",f5allCVEMedium.shape[0])
  print("- Low      :",f5allCVELow.shape[0])

  Excelwriter = pd.ExcelWriter(outputfile, engine='xlsxwriter')

  # All devices sheet
  f5AllDetails.to_excel(Excelwriter,sheet_name='All devices')


  # Hardware devices sheet
  f5Hardware.to_excel(Excelwriter,sheet_name='Hardware')
  hwWorksheet = Excelwriter.sheets['Hardware']
  hwWorksheet.set_column(0,0,25)
  hwWorksheet.set_column(1,1,10)

  hwWorkbook=Excelwriter.book
  hwWorksheet = Excelwriter.sheets['Hardware']
  hwChart=hwWorkbook.add_chart({'type': 'bar'})
  hwChart.set_title({
    'name': 'Hardware devices summary',
    'overlay': False
  })
  hwChart.add_series({
    'categories': '=Hardware!$A$2:$A$'+str(f5Hardware.shape[0]+1),
    'values': '=Hardware!$B$2:$B$'+str(f5Hardware.shape[0]+1),
    'fill': {'color': 'blue'}
  })
  hwChart.set_y_axis({
    'major_gridlines': {
      'visible': True,
      'line': {'width': .5, 'dash_type': 'dash'}
    },
  })
  hwChart.set_legend({'position': 'none'})
  hwWorksheet.insert_chart('F2', hwChart)


  # TMOS sheet
  allVersionSummary.to_excel(Excelwriter,sheet_name='TMOS')

  tmosWorkbook=Excelwriter.book
  tmosWorksheet = Excelwriter.sheets['TMOS']
  chart=tmosWorkbook.add_chart({'type': 'bar'})
  chart.set_title({
    'name': 'TMOS versions summary',
    'overlay': False
  })
  chart.add_series({
    'categories': '=TMOS!$A$2:$A$'+str(allVersionSummary.shape[0]+1),
    'values': '=TMOS!$B$2:$B$'+str(allVersionSummary.shape[0]+1),
    'fill': {'color': 'blue'}
  })
  chart.set_y_axis({
    'major_gridlines': {
      'visible': True,
      'line': {'width': .5, 'dash_type': 'dash'}
    },
  })
  chart.set_legend({'position': 'none'})
  tmosWorksheet.insert_chart('F2', chart)

  # CVE sheet
  f5allCVECriticalStyled = (f5allCVECritical.style.applymap(lambda v: 'background-color: %s' % 'red' if v == 'CRITICAL' else ''))
  f5allCVECriticalStyled.to_excel(Excelwriter,sheet_name='CVE')

  f5allCVEHighStyled = (f5allCVEHigh.style.applymap(lambda v: 'background-color: %s' % 'orange' if v == 'HIGH' else ''))
  f5allCVEHighStyled.to_excel(Excelwriter, sheet_name='CVE',startrow=len(f5allCVECritical)+1,header=False)

  f5allCVEMediumStyled = (f5allCVEMedium.style.applymap(lambda v: 'background-color: %s' % 'yellow' if v == 'MEDIUM' else ''))
  f5allCVEMediumStyled.to_excel(Excelwriter,sheet_name='CVE',startrow=len(f5allCVECritical)+len(f5allCVEHigh)+1,header=False)

  f5allCVELowStyled = (f5allCVELow.style.applymap(lambda v: 'background-color: %s' % 'green' if v == 'LOW' else ''))
  f5allCVELowStyled.to_excel(Excelwriter,sheet_name='CVE',startrow=len(f5allCVECritical)+len(f5allCVEHigh)+len(f5allCVEMedium)+1,header=False)

  cveWorksheet = Excelwriter.sheets['CVE']
  cveWorksheet.set_column(1,1,20)
  cveWorksheet.set_column(2,2,50)
  cveWorksheet.set_column(3,3,15)
  cveWorksheet.set_column(4,4,11)
  cveWorksheet.set_column(5,5,22)
  cveWorksheet.set_column(6,6,128)

  Excelwriter.save()
  print("Output file written to",outputfile)



if __name__ == "__main__":

  if len(sys.argv)!=3:
    print(sys.argv[0],"[json filename] [output xlsx filename]")
  else:
   bigiqXLS(jsonfile=sys.argv[1],outputfile=sys.argv[2])
