function renderTable(tableData) {
  // 渲染表格，tableData：后端返回的数据
  const { data: arrData, code, total } = JSON.parse(tableData);
  const data = arrData.map((e) => {
    e.sex = e.sex === "2" ? "女" : "男";
    e.symptoms_type = e.symptoms_type === "1" ? "肾阳虚" : "肾阴虚";
    return e;
  });
  layui.use(["laypage", "table", "layer", "form"], function () {
    const laypage = layui.laypage,
      layer = layui.layer,
      form = layui.form;
    const table = layui.table;
    // 表格table组件
    table.render({
      elem: ".info_table", // 定位表格ID
      title: "用户数据表",
      toolbar: "#headBar", // 表格头工具栏
      cols: tabelCols,
      data,
      limit: queryObj.limit, // 每一页数据条数
      done: function () {
        // 分页组件
        getPage(total, laypage);
      },
    });
    table.on("tool(test)", function (obj) {
      //行工具栏事件，点击详细的相关处理
      switch (obj.event) {
        case "detail": {
          id = obj.data.id;
          $.ajax({
            type: "POST",
            url: `http://127.0.0.1:5000/find_channelNumber`,
            data: {
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
                  cols: patientCols,
                  data: [data.find((e) => e.id === id)],
                  limit: queryObj.limit, // 每一页数据条数
                  done: function () {
                    // 分页组件
                    getPage(total, laypage);
                  },
                });
              }, 0);
              layer.open({
                type: 1,
                shadeClose: true,
                area: ["1200", "450"],
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
                channelSelect.append(
                  $(`<option value="">请选择一个通道</option>`)
                );
                for (let i = 1; i <= channelNumber; ++i) {
                  const newOption = $(`<option value=${i}>通道${i}</option>`);
                  channelSelect.append(newOption);
                }
              }
              form.render("select", "channel_form"); // 重新渲染select
            },
          });
        }
      }
    });
    table.on("toolbar(test)", function (obj) {
      // 点击查询按钮后的弹出层，用于更细节的查询
      var checkStatus = table.checkStatus(obj.config.id);
      switch (obj.event) {
        case "query": {
          layer_idx = layer.open({
            type: 1,
            shadeClose: true,
            title: "查询页面",
            content: $(".detail_query"),
          });
          break;
        }
        case "all_data": {
          queryObj = orignQuery;
          getTable(queryObj, true, layer, "重置成功!");
          $(".detail_query .layui-form")[0].reset();
        }
      }
    });
    form.on("select(channel_select)", function (data) {
      const { value } = data;
      $.ajax({
        type: "POST",
        url: `http://127.0.0.1:5000/channel_data`,
        data: {
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
    });
  });
}
function getTable(postData, sign = false, layer = null, msg = "") {
  $.ajax({
    // 向后端请求数据
    type: "POST", //请求的方法
    url: `http://127.0.0.1:5000/patient_info_by_condition`,
    data: postData, // 携带的数据，POST方法用
    success: function (returnData) {
      // 请求成功时的回调函数
      renderTable(returnData);
      if (sign) {
        layer.msg(msg);
        layer.close(layer_idx);
      }
    },
  });
}
function getPage(total, laypage) {
  // 设置分页
  laypage.render({
    elem: "demo", // 根据ID定位
    count: total, // 获取的数据总数
    limit: queryObj.limit, // 每页默认显示的数量，同上
    layout: ["prev", "page", "next", "limit"],
    curr: queryObj.page, // 页码
    jump: function (obj, first) {
      if (!first) {
        queryObj.page = obj.curr; // 设置当前页位置
        queryObj.limit = obj.limit; // 设置每页的数据条数
        getTable(queryObj);
      }
    },
  });
}
layui.use(["form", "layer"], function () {
  const form = layui.form,
    layer = layui.layer;
  form.verify({
    isNumber: (value) => {
      if (Number.isNaN(Number(value))) {
        return "请输入数字";
      }
    },
  });
  form.on("submit(*)", (data) => {
    const { field } = data;
    const QUERY_DATA = {
      id: field.id.trim(),
      sex: field.sex.trim(),
      symptoms: field.symptoms.trim(),
      age: JSON.stringify([field.age_min.trim(), field.age_max.trim()]),
      serum_creatinine: JSON.stringify([
        field.ser_min.trim(),
        field.ser_max.trim(),
      ]),
      eGFR: JSON.stringify([field.eGFR_min, field.eGFR_max.trim()]),
      page: 1,
      limit: 10,
    };
    queryObj = QUERY_DATA;
    getTable(queryObj, true, layer, "查询成功!");
    return false;
  });
});
layui.use(["element"], function () {});
let layer_idx = 0; // layer的index参数，用于控制弹出层（查询用）的关闭
let queryObj = {
  id: "",
  sex: "",
  symptoms: "",
  age: JSON.stringify(["", ""]),
  serum_creatinine: JSON.stringify(["", ""]),
  eGFR: JSON.stringify(["", ""]),
  page: 1,
  limit: 10,
}; // 查询字符串，用于获取病人的数据
let id = "";

const channelDom = $(".show_div")[0];
const channelSelect = $(".channel");
const orignQuery = { ...queryObj }; // 原始的查询字符串，用于重置操作
const channelChart = echarts.init(channelDom);
const tabelCols = [
  [
    {
      field: "id",
      title: "编号",
      width: 80,
      align: "center",
    },
    { field: "sex", title: "性别", width: 80, align: "center" },
    {
      field: "age",
      title: "年龄",
      width: 80,
      align: "center",
    },
    {
      field: "serum_creatinine",
      title: "血肌酐",
      width: 110,
      align: "center",
    },
    {
      field: "eGFR",
      title: "eGFR",
      width: 177,
      align: "center",
    },
    { field: "symptoms_type", title: "症型", align: "center" },
    { field: "tongue", title: "舌", align: "center" },
    { field: "pulse", title: "脉", align: "center" },
    {
      field: "detail",
      title: "详细",
      width: 80,
      toolbar: ".colBar",
      align: "center",
    },
  ],
];
const patientCols = [[...tabelCols[0]]];
patientCols[0].pop();
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
getTable(queryObj); // 获得表格数据，第一次调用默认获得所有病人的信息（第一页）
