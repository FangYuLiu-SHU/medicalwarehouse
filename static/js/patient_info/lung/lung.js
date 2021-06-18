layui.use(["form", "layer"], function () {
  const form = layui.form,
    layer = layui.layer;
  form.on("submit(lung)", (data) => {
    const { field } = data;
    const QUERY_LUNG_DATA = {
      page_el: "page_lung",
      table: "lung",
      id: field.id.trim(),
      wm_diagnosis: field.wm_diagnosis.trim(),
      tongue: field.tongue.trim(),
      pulse: field.pulse.trim(),
      sex: field.sex === undefined ? "" : field.sex.trim(),
      fei_qi_xu: field.fei_qi_xu === undefined ? "" : field.fei_qi_xu.trim(),
      pi_qi_xu: field.pi_qi_xu === undefined ? "" : field.pi_qi_xu.trim(),
      sheng_qi_xu:
        field.sheng_qi_xu === undefined ? "" : field.sheng_qi_xu.trim(),
      age: JSON.stringify([field.age_min.trim(), field.age_max.trim()]),
      FEV1: JSON.stringify([field.FEV1_min.trim(), field.FEV1_max.trim()]),
      FVC: JSON.stringify([field.FVC_min.trim(), field.FVC_max.trim()]),
      "FEV1%": JSON.stringify([
        field["FEV1%_min"].trim(),
        field["FEV1%_max"].trim(),
      ]),
      "FEV1/FVC": JSON.stringify([
        field["FEV1/FVC_min"].trim(),
        field["FEV1/FVC_max"].trim(),
      ]),
      PEF: JSON.stringify([field.PEF_min.trim(), field.PEF_max.trim()]),
      page: 1,
      limit: 10,
    };
    console.log(QUERY_LUNG_DATA);
    query_lung_obj = QUERY_LUNG_DATA;
    getTable(query_lung_obj, url, true, layer, "查询成功!");
    return false;
  });
});
function renderTable_lung(tableData) {
  // 渲染表格，tableData：后端返回的数据
  const { data: arrData, code, total } = JSON.parse(tableData);
  const data = arrData.map((e) => {
    e.sex = e.sex === "2" ? "女" : "男";
    e.symptoms_type = e.symptoms_type === "1" ? "肾阳虚" : "肾阴虚";
    return e;
  });

  layui.use(["laypage", "table", "layer", "form"], function () {
    const laypage = layui.laypage;
    const table = layui.table;
    table.render({
      elem: ".lung_info_table", // 定位表格ID
      title: "用户数据表",
      toolbar: "#headBar_lung", // 表格头工具栏
      cols: tabelCols,
      data,
      limit: query_lung_obj.limit, // 每一页数据条数
      done: function () {
        // 分页组件
        getPage(total, laypage, url, query_lung_obj);
      },
    });
    table.on("toolbar(lung)", function (obj) {
      // 点击查询按钮后的弹出层，用于更细节的查询
      var checkStatus = table.checkStatus(obj.config.id);
      switch (obj.event) {
        case "query": {
          layer_idx = layer.open({
            type: 1,
            area: "700px",
            shadeClose: true,
            title: "查询页面",
            content: $(".lung_detail_query"),
          });
          break;
        }
        case "all_data": {
          query_lung_obj = orignQuery;
          getTable(query_lung_obj, url, true, layer, "重置成功!");
          $(".lung_detail_query .layui-form")[0].reset();
        }
      }
    });
  });

}

let query_lung_obj = {
  page_el: "page_lung",
  table: "lung",
  id: "",
  sex: "",
  symptoms: "",
  age: JSON.stringify(["", ""]),
  serum_creatinine: JSON.stringify(["", ""]),
  eGFR: JSON.stringify(["", ""]),
  page: 1,
  limit: 10,
};
console.log(query_lung_obj);

/*

{
  table: "lung",
  id: "",
  wm_diagnosis: "",
  tongue: "",
  pulse: "",
  sex: "",
  fei_qi_xu: "",
  pi_qi_xu: "",
  sheng_qi_xu: "",
  age: JSON.stringify(["", ""]),
  FEV1: JSON.stringify(["", ""]),
  FVC: JSON.stringify(["", ""]),
  "FEV1%": JSON.stringify([
    "", ""]),
  "FEV1/FVC": JSON.stringify([
    "", ""]),
};

*/
