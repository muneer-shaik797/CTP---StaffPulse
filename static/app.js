document.addEventListener('DOMContentLoaded',()=>{
 const search=document.getElementById('employeeSearch');
 if(search){search.addEventListener('input',()=>{const q=search.value.toLowerCase();document.querySelectorAll('#employeesTable tbody tr').forEach(row=>row.style.display=row.innerText.toLowerCase().includes(q)?'':'none')})}
 const rows=window.employeeRows||[];
 const chartEl=document.getElementById('performanceChart');
 if(chartEl && window.Chart){new Chart(chartEl,{type:'bar',data:{labels:rows.map(x=>x.name),datasets:[{label:'Score',data:rows.map(x=>x.average),backgroundColor:'#267b58',borderRadius:6,maxBarThickness:32},{label:'Attendance',data:rows.map(x=>x.attendance),backgroundColor:'#d8ed9b',borderRadius:6,maxBarThickness:32}]},options:{maintainAspectRatio:false,responsive:true,plugins:{legend:{position:'bottom',labels:{usePointStyle:true,boxWidth:7,font:{size:10}}}},scales:{x:{grid:{display:false},ticks:{font:{size:10},color:'#758178'}},y:{beginAtZero:true,max:100,grid:{color:'#edf0e8'},ticks:{font:{size:9},color:'#879188'}}}}})}
 const bandEl=document.getElementById('bandChart');
 if(bandEl && window.Chart){const bands={'On track':0,'Monitor':0,'Needs review':0};rows.forEach(x=>{if(x.average>=75)bands['On track']++;else if(x.average>=60)bands['Monitor']++;else bands['Needs review']++});new Chart(bandEl,{type:'doughnut',data:{labels:Object.keys(bands),datasets:[{data:Object.values(bands),backgroundColor:['#5da879','#edc05b','#e78a73'],borderWidth:4,borderColor:'#fff'}]},options:{cutout:'70%',maintainAspectRatio:false,responsive:true,plugins:{legend:{display:false}}}})}
 const due=document.querySelector('input[name="due_date"]');if(due){const today=new Date();const local=new Date(today.getTime()-today.getTimezoneOffset()*60000).toISOString().slice(0,10);due.min=local;}
});
