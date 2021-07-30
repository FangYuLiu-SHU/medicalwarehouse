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
    let id = 0;
    // 表格table组件
    table.render({
      elem: ".kidney_info_table", // 定位表格ID
      title: "用户数据表",
      toolbar: "#headBar_kidney", // 表格头工具栏
      cols: tabelCols,
      data,
      limit: query_kidney_Obj.limit, // 每一页数据条数
      done: function () {
        // 分页组件
        getPage(total, laypage, url, query_kidney_Obj);
      },
    });
    table.on("tool(test)", (obj) => {
      id = obj.data.id;
      rowToolEvent(obj, patientCols, data, form, table, "kidney");
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
            content: $(".kidney_detail_query"),
          });
          break;
        }
        case "all_data": {
          query_kidney_Obj = orignQuery_kidney;
          getTable(query_kidney_Obj, url, true, layer, "重置成功!");
          $(".kidney_detail_query .layui-form")[0].reset();
        }
      }
    });
    form.on("select(channel_select)", (data) => {
      channel_select(data, id, "kidney");
    });
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
      page_el: "page_kidney",
      table: "kidney",
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
    query_kidney_Obj = QUERY_DATA;
    getTable(query_kidney_Obj, url, true, layer, "查询成功!");
    return false;
  });
});
layui.use(["element"], function () {});
let layer_idx = 0; // layer的index参数，用于控制弹出层（查询用）的关闭
let query_kidney_Obj = {
  page_el: "page_kidney",
  table: "kidney",
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

const orignQuery_kidney = { ...query_kidney_Obj }; // 原始的查询字符串，用于重置操作
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
getTable(query_kidney_Obj, url); // 获得表格数据，第一次调用默认获得所有病人的信息（第一页）
