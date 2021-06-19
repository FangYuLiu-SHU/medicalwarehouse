layui.use(["form", "layer"], function () {
    const form = layui.form,
      layer = layui.layer;
    form.on("submit(liver)", (data) => {
      const { field } = data;
      console.log(field);
      const QUERY_LIVER_DATA = {
        page_el: "page_liver",
        table: "liver",
        id: field.id.trim(),
        sex: field.sex.trim(),
        symptoms_type: field.symptoms_type.trim(),
        tongue: field.tongue.trim(),
        pulse: field.pulse.trim(),
        age: JSON.stringify([field.age_min.trim(), field.age_max.trim()]),
        ALT: JSON.stringify([field.ALT_min.trim(), field.ALT_max.trim()]),
        page: 1,
        limit: 10,
      };
      console.log(QUERY_LIVER_DATA);
      query_liver_obj = QUERY_LIVER_DATA;
      getTable(query_liver_obj, "/liver_patient_info", true, layer, "查询成功!");
      return false;
    });
  });
  function renderTable_liver(tableData) {
    // 渲染表格，tableData：后端返回的数据
    const { data: arrData, code, total } = JSON.parse(tableData);
    const data = arrData.map((e) => {
      e.sex = e.sex === "1" ? "女" : "男";
      e.symptoms_type = e.symptoms_type === "1" ? "肝胆湿热症" : "肝郁脾虚症";
      return e;
    });
    layui.use(["laypage", "table", "layer", "form"], function () {
      const laypage = layui.laypage;
      const table = layui.table;
      const form = layui.form;
      table.render({
        elem: ".liver_info_table", // 定位表格ID
        title: "用户数据表",
        toolbar: "#headBar_liver", // 表格头工具栏
        cols: tabelCols_liver,
        data,
        limit: query_liver_obj.limit, // 每一页数据条数
        done: function () {
          // 分页组件
          getPage(total, laypage, "/liver_patient_info", query_liver_obj);
        },
      });
      table.on("tool(liver)", obj => {
        id = obj.data.id;
        rowToolEvent(obj, patient_tabel_liver, data, form, table, "liver")
      });
      table.on("toolbar(liver)", function (obj) {
        // 点击查询按钮后的弹出层，用于更细节的查询
        var checkStatus = table.checkStatus(obj.config.id);
        switch (obj.event) {
          case "query": {
            layer_idx = layer.open({
              type: 1,
              shadeClose: true,
              title: "查询页面",
              content: $(".liver_detail_query"),
            });
            break;
          }
          case "all_data": {
            query_liver_obj = orignQuery_liver;
            getTable(query_liver_obj, "/liver_patient_info", true, layer, "重置成功!");
            $(".liver_detail_query .layui-form")[0].reset();
          }
        }
      });
      form.on("select(channel_select)", data => {channel_select(data, id, "liver")});
    });
  
  }
  
  let query_liver_obj = {
    page_el: "page_liver",
    table: "liver",
    id: "",
    tongue: "",
    pulse: "",
    sex: "",
    ALT: JSON.stringify(["", ""]),
    age: JSON.stringify(["", ""]),
    symptoms_type: ""
  };
  const orignQuery_liver = {...query_liver_obj}
  let tabelCols_liver = [
    [
      {
        field: "id",
        title: "编号",
        width: 155,
        align: "center",
      },
      { field: "sex", title: "性别", width: 80, align: "center" },
      {
        field: "age",
        title: "年龄",
        width: 80,
        align: "center",
      },
      { field: "ALT", title: "ALT", width: 80, align: "center" },
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
  ]
  let patient_tabel_liver = [[...tabelCols_liver[0]]]
  patient_tabel_liver[0].pop()
  
  