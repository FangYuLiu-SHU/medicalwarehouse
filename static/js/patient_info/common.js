function getTable(postData, dir, sign = false, layer = null, msg = "") {
  console.log(dir);
  console.log(postData);
  $.ajax({
    // 向后端请求数据
    type: "POST", //请求的方法
    url: dir,
    data: postData, // 携带的数据，POST方法用
    success: function (returnData) {
      // 请求成功时的回调函数
      switch (postData.table) {
        case "kidney":
          renderTable(returnData);
          break;
        case "lung":
          renderTable_lung(returnData);
          break;
        case "liver":
          renderTable_liver(returnData);
          break;
      }
      if (sign) {
        layer.msg(msg);
        layer.close(layer_idx);
      }
    },
  });
}

function getPage(total, laypage, dir, queryObj) {
  // 设置分页
  laypage.render({
    elem: queryObj.page_el, // 根据ID定位
    count: total, // 获取的数据总数
    limit: queryObj.limit, // 每页默认显示的数量，同上
    layout: ["prev", "page", "next", "limit"],
    curr: queryObj.page, // 页码
    jump: function (obj, first) {
      if (!first) {
        queryObj.page = obj.curr; // 设置当前页位置
        queryObj.limit = obj.limit; // 设置每页的数据条数
        getTable(queryObj, dir);
      }
    },
  });
}

let url = "/patient_info_by_condition";

layui.use(["element"], function () {
  const element = layui.element;
  element.on("tab(patient)", function (data) {
    switch (data.index) {
      case 0:
        getTable(query_kidney_Obj, "/patient_info_by_condition");
        break;
      case 1:
        getTable(query_liver_obj, "/liver_patient_info");
        break;
      case 2:
        getTable(query_lung_obj, "/lung_patient_info");
        break;
    }
  });
});

function rowToolEvent(obj, cols, data, form, table, type) {
  //行工具栏事件，点击详细的相关处理
  switch (obj.event) {
    case "detail": {
      let id = obj.data.id;
      $.ajax({
        type: "POST",
        url: `/find_channelNumber`,
        data: {
          type,
          id,
        }, // 携带的数据，POST方法用
        success: function (returnData) {
          let { channelNumber } = JSON.parse(returnData);
          channelNumber = parseInt(channelNumber);
          setTimeout(() => {
            //使用计时器，防止表格渲染出现格式问题
            table.render({
              elem: ".patient_info", // 定位表格ID
              title: "病人信息",
              cols,
              data: [data.find((e) => e.id === id)],
              limit: query_kidney_Obj.limit, // 每一页数据条数
            });
          }, 0);
          layer.open({
            type: 1,
            shadeClose: true,
            resize: false,
            area: "1000px",
            title: "详细信息",
            content: $(".patient_detail"),
            end: () => {
              channelChart.clear();
            }, // 弹出层关闭后的回调， 清除eCharts图表
          });
          channelSelect.empty(); // 清空select中的option选项， 防止冲突
          if (channelNumber === 0) {
            channelSelect.append(
              $(`<option value="none" disabled>没有数据</option>`)
            );
          } else {
            channelSelect.append($(`<option value="">请选择一个通道</option>`));
            for (let i = 1; i <= channelNumber; ++i) {
              const newOption = $(`<option value=${i}>通道${i}</option>`);
              channelSelect.append(newOption);
            }
          }
          form.render("select", "channel_form"); // 重新渲染select
        },
      });
      $.ajax({
        type: "POST",
        url: `/tongue_data`,
        data: {
          id,
          patient: type,
        },
        success: function (data) {
          const { tongue_data } = data;
          tougeImg.attr("src", baseURL + tongue_data);
        },
      });
    }
  }
}

function channel_select(data, id, type) {
  const { value } = data;
  $.ajax({
    type: "POST",
    url: `http://127.0.0.1:5000/channel_data`,
    data: {
      type,
      id,
      num: value,
    }, // 携带的数据，POST方法用
    success: function (returnData) {
      layer.msg("更新成功");
      const { data } = JSON.parse(returnData),
        len = data.length;
      let xaxis = [];
      for (let i = 1; i <= len; ++i) {
        xaxis.push(i);
      }
      option.xAxis.data = xaxis;
      option.series.data = data;
      channelChart.setOption(option);
    },
  });
}

const baseURL = "data:;base64,";
const tougeImg = $(".touge_img img");
const channelDom = $(".show_div")[0];
const channelSelect = $(".channel");
const channelChart = echarts.init(channelDom);
const option = {
  title: {
    text: "脉搏信号",
    left: "1%",
  },
  tooltip: {
    trigger: "axis",
  },
  grid: {
    left: "10%",
    right: "15%",
    bottom: "10%",
  },
  xAxis: {
    data: [],
  },
  yAxis: {
    min: "dataMin",
    max: "dataMax",
    axisLabel: {
      formatter: (value) => value.toFixed(4),
    },
  },
  dataZoom: [
    {
      startValue: "1",
    },
    {
      type: "inside",
    },
  ],
  series: {
    name: "脉搏信号",
    type: "line",
    data: [],
    markLine: {
      silent: true,
      lineStyle: {
        color: "#333",
      },
    },
  },
};
