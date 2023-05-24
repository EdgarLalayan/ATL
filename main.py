
import fitz
import base64
import argparse
import json
import re
import io
import ocrmypdf
import requests
import csv
import concurrent.futures

class PDFParser:
    def __init__(self):
        self.result = {
            "Client":None,
            'Vendor': None,
            'Date': None,
            'MonthlyCost': None
        }   
        self.pattern = r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}"
        self.VENDORS_CSV = 'vendors.csv'
    def get_text(self,pdf,ocr=True):
        text = self._pdf_to_text(pdf,ocr=ocr)
        return text

    def text_file(self,pdf):
        b64 = self._pdf_to_b64(pdf)
        with open(f'{pdf[:-3]}txt', 'w') as file:
            file.write(b64)
    
    def parsePDF(self,pdf,ocr=True):
        data = self._pdf_to_text(pdf,ocr=ocr)
        self._document_checker(data)
        return self.result


    def _pdf_to_text(self,pdf,scanned=False,ocr=True):
        if pdf.endswith('.txt'):
            with open(pdf, 'r') as f:
                b64_string = f.read()
        elif pdf.startswith('http'):
            response = requests.get(pdf)
            pdf_as_binary_string = response.content
            b64_string = base64.b64encode(pdf_as_binary_string).decode('utf-8')
        else:
            b64_string = self._pdf_to_b64(pdf)
        
        datas = []
        
        pdf_as_binary_string = base64.b64decode(b64_string)
        binary_stream = io.BytesIO(pdf_as_binary_string)
        try:
            pdf_file = fitz.open(stream=binary_stream, filetype='pdf')
        except fitz.fitz.FileDataError:
            datas = self._scanned_pdf_to_txt(binary_stream)
            return datas


        for page_num in range(pdf_file.page_count):
            page = pdf_file[page_num]
            page_text = page.get_text()
            data = page_text.replace('\n', '|')
            datas.append(data)
        joined = ''.join(datas)
        joined = joined.replace('●','').replace('•','')
        if joined !='':
            lst = joined.split()
            for i in lst:
                i
                if i.count('�') > 1 :
                    scanned = True
                    break
            
        elif joined == '':
            scanned = True
        
        if scanned == True and ocr == True:
            datas = self._scanned_pdf_to_txt(binary_stream)
            return datas
        else:
            return datas

    def _document_checker(self,data):
        joined_data = '|'.join(data)

        csv_file = self.VENDORS_CSV 
        all_vendors_list = []
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                all_vendors_list.append(row[0])

        # The order of elements in found_elements depends on the order of elements 
        # in all_vendors_list and the order in 
        # which they are found in the joined_data.
        
        dataForVendor = joined_data
        tryVendors = ['Atlas','WiLine',"Quality Voice & Data"]
        #Remove exception
        exception = ['Microsoft Customer',"DocuSign"]
        pattern = r'\b' + r'\b|\b'.join(re.escape(element) for element in exception) + r'\b'
        dataForVendor = re.sub(pattern, '', dataForVendor)
       
        found_elements = [element for element in all_vendors_list if re.findall(r'\b' + re.escape(element) + r'\b', dataForVendor,re.IGNORECASE)]
        found_elements = sorted(found_elements, key=len, reverse=True)
        #print("found_elements:",found_elements)
        if found_elements:
            pattern = r'\b(?:' + '|'.join(re.escape(element) for element in found_elements) + r')\b'
            matches = re.findall(pattern, dataForVendor,re.IGNORECASE)
            matche = [item for i, item in enumerate(matches) if item not in matches[:i]][0]
            desired_matche = next((element for element in found_elements if element.lower() == matche.lower()), None)
            self.result["Vendor"] = desired_matche
        
        elif not found_elements:
            found_elements = [element for element in tryVendors if re.findall(r'\b' + re.escape(element) + r'\b', dataForVendor,re.IGNORECASE)]
            found_elements = sorted(found_elements, key=len, reverse=True)
            #print("found_elements:",found_elements)
            if found_elements:
                pattern = r'\b(?:' + '|'.join(re.escape(element) for element in found_elements) + r')\b'
                matches = re.findall(pattern, dataForVendor,re.IGNORECASE)
                matches = [element for element in found_elements if element in dataForVendor]
                matche = [item for i, item in enumerate(matches) if item not in matches[:i]][0]
                desired_matche = next((element for element in found_elements if element.lower() == matche.lower()), None)
                self.result["Vendor"] = matche


        if 'Lumen' in joined_data:
            self._parse_lumen(joined_data)
        elif 'ClearFreight' in joined_data or 'clearfreight'  in joined_data:
            self._parse_clear_freight(joined_data)
        elif 'CenturyLink' in joined_data:
            self._parse_century_link(joined_data)
        elif 'ACC BUSINESS' in joined_data:
            self._parse_acc_business(joined_data)
        elif 'RingCentral' in joined_data:
             self._parse_ring_central(joined_data)
        elif '8x8' in joined_data:
            self._parse_x8x8(joined_data)
        elif  'TPx' in joined_data:
             self._parse_tpx(joined_data)
        elif 'Community Health Centers' in joined_data or 'CCHC' in joined_data:
            self._parse_cchc(joined_data)
        elif 'Claremont Lincoln University' in joined_data:
            self._parse_clu(joined_data)
        elif 'Sky Data Vault' in joined_data or 'SKY DATA VAULT' in joined_data:
            self._parse_sky_data(joined_data)
        elif 'pankow' in joined_data.lower():
            self._parse_pankow(joined_data)
        elif 'WiLine' in joined_data:
            self._parse_wiline(joined_data)
        elif 'AT&T' in joined_data:
            self._parse_att(joined_data)
        elif 'Talkdesk' in joined_data:
            self._parse_talkdesk(joined_data)
        elif 'Ushio America' in joined_data:
            self._parse_ushio_america(joined_data)


        
        else:
            print("Could not identify PDF.")   
    
    #Ushio America
    def _parse_ushio_america(self,joinedData):
        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            #DATA
            if 'Document completed by all-parties on' in lst[0] :
                self.result['Date'] = lst[1]


            #MonthlyCost
            if 'Total Non-Recurring Charges' in lst[0] or 'Monthly Total' in lst[0]:
                if '$' in lst[1]:
                    self.result['MonthlyCost'] = lst[1]
        

            del lst[0]
        self.result['Client'] = "Ushio America"
        if self.result['Date'] == None:
            dates = re.findall(self.pattern,joinedData)
            if len(dates) != 0:
                self.result['Date'] = dates[-1]

    #Talkdesk, Inc.
    def _parse_talkdesk(self,joinedData):
        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            #DATA
            if 'Date:' in lst[0] :
                pass

            #MonthlyCost
            if 'Talkdesk Licenses' in lst[0] or 'Credit Commit' in lst[0]:
                if '$' in lst[3]:
                    self.result['MonthlyCost'] = lst[3]

            del lst[0]
        self.result['Client'] = "Talkdesk, Inc."

    #AT&T
    def _parse_att(self,joinedData):
        pass

    #(Pankow)WiLine
    def _parse_wiline(self,joinedData):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            #DATA
            if 'Date:' in lst[0] :
                if any(month in lst[1] for month in months):
                    self.result['Date'] = lst[1].strip()

            #MonthlyCost
            if 'Total' ==  lst[0].strip():
                if '$' in lst[1]:
                    self.result['MonthlyCost'] = lst[1]
            del lst[0]
        self.result['Client'] = "WiLine"

    #Pankow
    def _parse_pankow(self,joinedData):
        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            #DATA
            if 'Date' in lst[0] and '/' in lst[2] and len(lst[2]) < 12:
                self.result['Date'] = lst[2].strip()
            elif 'Agreement Generation Date:' in lst[0] and '/' in lst[2]:
                self.result['Date'] = lst[2].strip()
            

            #MonthlyCost
            if 'Total Charges' in  lst[0]:
                if '$' in lst[1] or '$' in lst[2]:
                    self.result['MonthlyCost'] = lst[1]
            elif 'Total Monthly Recurring Charges' in lst[0] and lst[1][0].isnumeric():
                self.result['MonthlyCost'] = lst[1]
                
            
            del lst[0]
        self.result['Client'] = "Charles Pankow Builders"
        if self.result['Date'] == None:
            dates = re.findall(self.pattern,joinedData)
            if len(dates) != 0:
                self.result['Date'] = dates[-1]

    #Sky Data
    def _parse_sky_data(self,joinedData):
        #dates = re.findall(self.pattern,joinedData)
        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            #DATA

            #MonthlyCost
            if 'Total Monthly Cost' in  lst[0]:
                if lst[1].strip() == '$':
                    self.result['MonthlyCost'] = lst[2]+' $'
                elif lst[2].strip() == '$':
                    self.result['MonthlyCost'] = lst[1]+' $'
            
            del lst[0]
        self.result['Client'] = "Sky Data Vault, LLC"

    #Claremont Lincoln University
    def _parse_clu(self,joinedData):
        dates = re.findall(self.pattern,joinedData)
        if 'Spectrum Enterprise' in joinedData:
            self.result['Date'] = dates[-1]
        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            
            #Date
            if  'Date:' in lst[0] and '/' in lst[0]:
                self.result["Date"] = lst[0].split(":")[1].strip()
            
            #MonthlyCost
            if 'Total Monthly Recurring Charges' in lst[0]:
                if '$' in lst[1] or '$' in lst[2]:
                    self.result['MonthlyCost'] = lst[1]

            del lst[0]
        self.result['Client'] = "Claremont Lincoln University"
        if self.result['Date'] == None:
            self.result['Date'] = dates[-1]
    
    #ClearFreight
    def _parse_clear_freight(self,joinedData):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        monthsShort = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        dates = re.findall(self.pattern,joinedData)

        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            
            #Date
            if  'Document completed by all parties on' in lst[0]:
                self.result["Date"] = lst[1].strip()
            elif 'Circuit Provisioning' in joinedData:
                if any(month in lst[0] for month in months):
                    self.result["Date"] = lst[0].strip()
            elif 'Date:' in lst[0] and '/' in lst[0]:
                self.result["Date"] = lst[0].split(':')[1].strip()
            elif any(month in lst[0] for month in months) and 'Terms of Service' in lst[1]:
                self.result["Date"] = lst[0].strip()



            #MonthlyCost
            if 'Monthly Licensing Costs' in lst[0] and '$' in lst[1]:
                self.result['MonthlyCost'] = lst[1]
            elif 'Total Monthly:' in lst[0] and '$' in lst[0]:
                self.result['MonthlyCost'] = lst[0].split(':')[1]
            elif 'per month' in lst[0] and '$' in lst[1]:
                 self.result['MonthlyCost'] = lst[1].strip()

            del lst[0]

        self.result['Client'] = "ClearFreight"
    
    #CCHC   Comprehensive Community Health Centers
    def _parse_cchc(self,joinedData):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        dates = re.findall(self.pattern,joinedData)

        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            #Date
            if 'CCHC' in joinedData and 'Accepted On' in lst[0]:
                self.result["Date"] = lst[1].strip()
            elif 'Circuit Provisioning' in joinedData or 'Date:' in lst[0]:
                if any(month in lst[0] for month in months):
                    self.result["Date"] = lst[0].strip()

            
            #Cost
            if 'CCHC' in joinedData and 'Monthly price' in lst[0] and '$' in lst[1]:
                self.result['MonthlyCost'] = lst[1]
            elif ('per month'in lst[0] or 'Total' in lst[0])  and '$' in lst[1]:
                self.result['MonthlyCost'] = lst[1]
            elif 'Talkdesk Licenses' in lst[0] or 'Credit Commit' in lst[0]:
                if '$' in lst[3]:
                    self.result['MonthlyCost'] = lst[3]
            del lst[0]

        self.result['Client'] = "Comprehensive Community Health Centers"
        
        if self.result['Date'] == None:
            if len(dates) != 0:
                self.result['Date'] = dates[-1]
    
    #8x8
    def _parse_x8x8(self,joinedData):
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        lst = joinedData.split('|') 
        while True:
            if len(lst) == 0:
                break
            #Date
            if any(month in lst[0] for month in months) and self.result["Date"] == None:
                self.result["Date"] = lst[0].strip()
            elif 'Date:' in lst[0] and any(month in lst[1] for month in months) and self.result["Date"] == None:
                self.result["Date"] = lst[1].strip()+f' {lst[2]}'+lst[3]

            #MonthlyCost
            if 'Location Total' in lst[0]:
                self.result["MonthlyCost"] = lst[1].strip()
            del lst[0]
        self.result['Client'] = '8x8,inc.'

    #TPx
    def _parse_tpx(self,joinedData):
        lst = joinedData.split('|')
        while True:
            if len(lst) == 0:
                break
            #Date
            if 'DL' in lst[0] and '/' not in lst[1] and self.result['Date'] == None :
                del lst[0]
                continue
            elif  'DL' in lst[0] and '/'  in lst[1] and self.result['Date'] == None :
                date = lst[1].split()[0]
                self.result["Date"] = date  
            #Cost
            if 'Totals'in lst[0] :
                self.result['MonthlyCost'] = lst[2]
            elif 'Charge' == lst[0].strip():
                if lst[1].strip() and '$' in lst[3]:
                    self.result['MonthlyCost'] = lst[3]
                    


            del lst[0]

        self.result['Client'] = "TPx"

    #RingCentra, inc.
    def _parse_ring_central(self,joinedData):
        lst = joinedData.split('|')
        dates = re.findall(self.pattern,joinedData)
        self.result["Date"] = dates[-1]
        while True:
            if len(lst) == 0:
                break
            #Cost
            if 'Total Initial Amount *' in lst[0] and '$' in lst[1]:
                cost = lst[1].strip()
                self.result["MonthlyCost"] = cost    
            del lst[0]

        self.result['Client'] = "RingCentra, inc."

    #ACC BUSINESS          
    def _parse_acc_business(self,joinedData):
        lst = joinedData.split('|')        
        while True:
            if len(lst) == 0:
                break
            if '/' in lst[0] and lst[0].count('/') == 2  and "Updated" not in lst[0]:
                self.result["Date"] = lst[0]
            #Cost
            if 'Optional Service Charges:' in lst[0] and '$' in lst[1]:
                cost = lst[1].strip()
                self.result["MonthlyCost"] = cost
                
            del lst[0]
        
        self.result['Client'] = "ACC Business"

    #CenturyLink
    def _parse_century_link(self,joinedData):
        lst = joinedData.split('|')
        while True:
            if len(lst) == 0:
                break
            #Data
            if 'POPSUGAR' in lst[0] and '/' in lst[1]:
                date = lst[1].strip()
                self.result["Date"] = date
            del lst[0]
        self.result["Vendor"] = "CenturyLink"

    #Lumen 
    def _parse_lumen(self, joined_data):
        lst = joined_data.split('|')
        while True:
            if len(lst) == 0:
                break
            if 'Quote' in lst[0]:
                self.result["Date"] = lst[1].strip()
            # Cost
            if 'Monthly Recurring Charges' in lst[0]:
                cost = lst[0].split(':')[1].strip()
                self.result["MonthlyCost"] = cost
                del lst[0]
            if 'Monthly Recurring' in lst[0]:
                cost = lst[1].strip()
                self.result["MonthlyCost"] = cost
            # Data
            if 'Document Generation Date:' in lst[0]:
                date = lst[0].split(':')[1].strip()
                self.result["Date"] = date
            del lst[0]
        self.result["Vendor"] = "Lumen"
       
    def _process_page(self,page):
        page_text = page.get_text()
        data = page_text.replace('\n', '|')
        return data

    def _scanned_pdf_to_txt(self, input_file):
        with io.BytesIO() as output_buffer:
            ocrmypdf.ocr(input_file, output_buffer, force_ocr=True)
            output_buffer.seek(0)
            pdf = fitz.open(stream=output_buffer.read(), filetype='pdf')
            datas = []

            with concurrent.futures.ThreadPoolExecutor() as executor:
                page_futures = [executor.submit(self._process_page, page) for page in pdf]
                datas = [future.result() for future in concurrent.futures.as_completed(page_futures)]
        return datas

    def _pdf_to_b64(self,pdf):
        with open(pdf, "rb") as pdf_file:
            pdf_data = pdf_file.read()

        pdf_b64_string = base64.b64encode(pdf_data).decode("utf-8")

        return pdf_b64_string
    
    def dictToJson(self,res):
        with open('file.json', 'w') as f:
            json.dump(res, f, indent=2)
        with open('file.json', 'r') as f:
            print(f.read())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--argument', required=False)
    args = parser.parse_args()
    argument_value = args.argument
    parser = PDFParser()
    res = parser.parsePDF(argument_value,ocr=True)
    parser.dictToJson(res)

#======================#
#       TESTING        #
#======================#
# pdf = '/Users/edgarlalayan/Desktop/CASPIO/ATL/Contracts/USHIO/USHIOAMERICA2.pdf'
# parser = PDFParser()
# res = parser.parsePDF(pdf,ocr=True)
# #res = parser.get_text(pdf)
# print(res)



