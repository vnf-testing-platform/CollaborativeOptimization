"use strict";

var line = document.getElementById("line-chart");
var area = document.getElementById("area-chart");
var bar = document.getElementById("bar-chart");
var pie = document.getElementById("pie-chart");
var polar = document.getElementById("polar-chart");
var radar = document.getElementById("radar-chart");

var options ={
    scales: {
        yAxes: [{
            ticks: {
                beginAtZero:true
            }
        }]
    }
};

/**
 *
 * @type {{labels: [*], datasets: [*]}}

//LINE CHART EXAMPLE
// =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
var dataLine = {
    labels: ["10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30", "10:35", "10:40", "10:45", "10:50", "10:55", "11:00", "11:05"],
    datasets: [
        {
            label: "CPU",
            fill: false,
            backgroundColor: "#FFCE56",
            borderColor: "#FFCE56",
            borderCapStyle: 'butt',
            borderDash: [],
            borderDashOffset: 0.0,
            borderJoinStyle: 'miter',
            pointBorderColor: "rgba(75,192,192,1)",
            pointBackgroundColor: "#fff",
            pointBorderWidth: 1,
            pointHoverRadius: 5,
            pointHoverBackgroundColor: "#FFCE56",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            pointHoverBorderWidth: 2,
            pointRadius: 1,
            pointHitRadius: 10,
            data: [55, 79, 70, 75, 88, 55, 79, 70, 75, 88, 78, 83, 76,0],
            spanGaps: false
        }
    ]
};
var lineChart = new Chart(line, {
    type: 'line',
    data: dataLine
});


//AREA CHART EXAMPLE
// =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
var dataArea = {
    labels: ["10:00", "10:05", "10:10", "10:15", "10:20", "10:25", "10:30", "10:35", "10:40", "10:45", "10:50", "10:55", "11:00"],
    datasets: [
        {
            label: "Memery",
            fill: true,
            backgroundColor: "rgba(55, 209, 119, 0.45)",
            borderColor: "rgba(55, 209, 119, 0.45)",
            pointBorderColor: "rgba(75,192,192,1)",
            pointBackgroundColor: "#fff",
            pointHoverBackgroundColor: "343d3e",
            pointHoverBorderColor: "rgba(220,220,220,1)",
            data: [12, 13, 11, 6, 9, 12, 13, 11, 6, 9, 7,11,8]
        },
    ],
    options: {
        scales: {
            yAxes: [{
                stacked: true
            }]
        }
    }
};

var areaChart = new Chart(area, {
    type: 'line',
    data: dataArea,
    options: options

});

  */
//BAR CHART EXAMPLE
// =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
var dataBars = {
    labels: ["64K", "128K", "256K", "512K", "1024K", "1280K", "1518K"],
    datasets: [
        {
            label: "最小时延",
            fill: true,
            backgroundColor: "rgba(179,181,198, 0.75)",
            borderColor: "rgba(179,181,198, 1)",
            data: [10, 11, 8, 4, 8, 11, 9]
        },
        {
            label: "平均时延",
            fill: true,
            backgroundColor: "rgba(75, 192, 192,0.75)",
            borderColor: "rgba(75, 192, 192,1)",
            data: [12, 13, 11, 6, 9, 14, 10]
        },
        {
            label: "最大时延",
            fill: true,
            backgroundColor: "rgba(255, 159, 64, 0.75)",
            borderColor: "rgba(255, 159, 64, 1)",
            data: [14, 15, 12, 9, 11, 15, 13]
        },

    ],
    options: {
        scales: {
            yAxes: [{
                stacked: true
            }]
        }
    }
};

// var barChar = new Chart(bar, {
//     type: 'bar',
//     data: dataBars,
//     options: options
//
// });

//vBarsCPU利用率
// =-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=
$(function(){
    //整个html页面刷新
    setInterval(refresh,500);
    function refresh(){
             $.ajax('/api/v1/if-exist-current-task/', {
        method: 'POST',
        data:
          JSON.stringify({
                  flag: 1,
                  //csrfmiddlewaretoken: $('input[type=hidden]').val()
              }),
      }).done(function (data) {
          //存在或不存在current-task时不同的表现
         //alert(data.taskid);
         var taskId = data.taskid;
         switch(data.tasktype)
                  {
                      case 'VNF_1_Concurrent_Session_Capacity':
                          var taskType = '1';
                          break;
                      case 'VNF_2_VBRAS_Client_Forwarding_Performance':
                          var taskType = '2';
                          break;
                      case 'VNF_3_PPPoE_IPTV_IPoE_VoIP':
                          var taskType = '3';
                          break;
                  }
         if(data.taskid){
              $.ajax('/api/v1/index-get-cpu-memory', {
                method: 'POST',
                data:
                  JSON.stringify({
                      taskid: taskId,
                  }),
                });
              $.ajax('/api/v1/get-index-cpu/', {
                method: 'POST',
                data:
                  JSON.stringify({
                      taskid: taskId,
                      flag: 1,
                      //csrfmiddlewaretoken: $('input[type=hidden]').val()
                  }),
              }).done(function (data) {
                  //alert(data[0]['add_time']);
                  var curLabels_CPU = [];   // times, x axis
                  var curDatasets_CPU = []; // dataset
                  var curData_CPU = [];
                  data.forEach(function (item) {
                      curLabels_CPU.push(item['add_time']);
                      curData_CPU.push(item['cpu']);
                  });
                  curDatasets_CPU.push({
                      label: 'cpu',
                      fill: true,
                      backgroundColor: 'rgba(255, 206, 86, 0.4)',
                      borderColor: 'rgba(179,181,198,1)',
                      pointBackgroundColor: 'rgba(179,181,198,1)',
                      pointBorderColor: '#fff',
                      pointRadius: 4,
                      data: curData_CPU,
                  });

                  line = new Chart(document.getElementById("line-chart"), {
                      type: 'line',
                      data: {
                          labels: curLabels_CPU,
                          datasets: curDatasets_CPU,
                      }
                  });
              })

             $.ajax('/api/v1/get-index-memory/', {
                method: 'POST',
                data:
                  JSON.stringify({
                      taskid: taskId,
                      flag: 1,
                  }),
              }).done(function (data) {
                  var curLabels_Memory = [];   // times, x axis
                  var curDatasets_Memory = []; // dataset
                  var curData_Memory = [];
                  data.forEach(function (item) {
                      curLabels_Memory.push(item['add_time']);
                      curData_Memory.push(item['memory']);
                  });
                  curDatasets_Memory.push({
                      label: 'memory',
                      fill: true,
                      backgroundColor: "rgba(55, 209, 119, 0.45)",
                      borderColor: "rgba(55, 209, 119, 0.45)",
                      pointBorderColor: "rgba(75,192,192,1)",
                      pointBackgroundColor: "#fff",
                      pointHoverBackgroundColor: "343d3e",
                      pointHoverBorderColor: "rgba(220,220,220,1)",
                      data: curData_Memory,
                  });

                  line = new Chart(document.getElementById("area-chart"), {
                      type: 'line',
                      data: {
                          labels: curLabels_Memory,
                          datasets: curDatasets_Memory,
                      }
                  });
              })

              $.ajax('/api/v1/index-task-details', {
                method: 'POST',
                data:
                  JSON.stringify({
                      taskid: taskId,
                      tasktype:taskType,
                      flag: 1,
                  }),
              }).done(function (data) {
                  var currentData = '<h6>已完成session数：'+ data.current_session +'</h6>' +
                                '<h6>已完成：<span class="code">'+ data.current_session/data.set_session*100 +'%</span></h6>'
                  switch(taskType)
                  {
                      case '1':
                          var taskTypeTitle = 'PPPOE并发会话容量测试';
                          var taskDetail = '';
                          break;
                      case '2':
                          var taskTypeTitle = 'vBRAS用户侧转发性能测试';
                          var taskDetail = '<h6>64字节 平均时延 <span class="code" id="FS_64">' + data.frame_size_64 + 'μs</span></h6>' +
                                '<h6>128字节 平均时延 <span class="code" id="FS_128">' + data.frame_size_128 + 'μs</span></h6>' +
                                '<h6>256字节 平均时延 <span class="code" id="FS_256">' + data.frame_size_256 + 'μs</span></h6>' +
                                '<h6>512字节 平均时延 <span class="code" id="FS_512">' + data.frame_size_512 + 'μs</span></h6>' +
                                '<h6>1024字节 平均时延 <span class="code" id="FS_1024">' + data.frame_size_1024 + 'μs</span></h6>' +
                                '<h6>1280字节 平均时延 <span class="code" id="FS_1280">' + data.frame_size_1280 + 'μs</span></h6>' +
                                '<h6>1518字节 平均时延 <span class="code" id="FS_1518">' + data.frame_size_1518 + 'μs</span></h6>'
                          break;
                      case '3':
                          var taskTypeTitle = 'vBRAS综合上网业务测试';
                          var taskDetail = '<h6>测试业务：宽带上网（PPPoE）+ IPTV（PPPoE）+ ITMS（IPoE）+ VoIP（IPoE）</h6>'
                          break;
                  }

                  var currentTask = '<div class="timeline-box">' +
                            '<div class="timeline-icon bg-primary">' +
                                '<i class="fa fa-tasks"></i>' +
                            '</div>' +
                            '<div class="timeline-content">' +
                                '<h4 class="tl-title">正在运行的测试用例</h4>' +
                                '<p class="text-bold">' + taskTypeTitle + '</p>' +
                                '<h6>测试session数：'+ data.set_session +'</h6>' +
                                currentData + taskDetail +
                            '</div>' +
                            '<div class="timeline-footer">' +
                                '<span>开始时间：' + data.begin_time + '</span>' +
                            '</div>' +
                        '</div>'

                  var reportedTask = '<div class="timeline-box">' +
                            '<div class="timeline-icon bg-primary">' +
                                '<i class="fa fa-file"></i>' +
                            '</div>' +
                            '<div class="timeline-content">' +
                                '<h4 class="tl-title">生成报告</h4>' +
                                '<p class="text-bold">' + taskTypeTitle + '</p>' +
                                '<h6>测试session数：'+ data.set_session +'</h6>' + taskDetail +
                            '</div>' +
                            '<div class="timeline-footer">' +
                                '<span>开始时间：' + data.begin_time + '</span>' +
                            '</div>' +
                        '</div>'
                   var completedTask = '<div class="timeline-box">' +
                            '<div class="timeline-icon bg-primary">' +
                                '<i class="fa fa-check"></i>' +
                            '</div>' +
                            '<div class="timeline-content">' +
                                '<h4 class="tl-title">测试完成</h4>' +
                                '<p class="text-bold">' + taskTypeTitle + '</p>' +
                                '<h6>测试session数：'+ data.set_session +'</h6>' + taskDetail +
                            '</div>' +
                            '<div class="timeline-footer">' +
                                '<span>开始时间：' + data.begin_time + '</span>' +
                            '</div>' +
                        '</div>'

                  var taskTimeLine = $('#taskTimeLine');
                  taskTimeLine.children().remove();

                  $('#taskTimeLine').append(currentTask);
                  $('#taskTimeLine').append(reportedTask);
                  $('#taskTimeLine').append(completedTask);
              })

         }else{
             alert("没有正在运行的测试用例！")
         }
     });
    }
});
