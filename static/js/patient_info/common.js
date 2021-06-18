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
      switch(postData.table) {
        case "kidney": renderTable(returnData);break;
        case "lung": renderTable_lung(returnData);break;
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
let urlArr = ["/patient_info_by_condition", "/patient_info_by_condition", "http://127.0.0.1:5000/lung_patient_info"]

layui.use(["element"], function() {
  const element = layui.element;
  element.on('tab(patient)', function(data){
    url = urlArr[data.index]
    getTable(query_lung_obj, url);
  });  
})