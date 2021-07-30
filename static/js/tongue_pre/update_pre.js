function showProgress(percent, filter, element) {
  element.progress(filter, `${percent}%`);
}
layui.use("element", function () {
  const element = layui.element;
  $(".imgFile").on("change", (e) => {
    const { files } = e.target;
    let reads = new FileReader();
    imgData = new FormData();
    reads.readAsDataURL(files[0]);
    imgData.append("tongueImg", files[0]);
    $imgProgress.show();
    $showImg.hide();
    reads.onload = (e) => {
      $imgProgress.hide();
      $showImg.show();
      showProgress(0, "imgUpload", element);
      $showImg.attr("src", e.target.result);
    };
    reads.onprogress = (e) => {
      showProgress(Math.ceil((e.loaded / e.total) * 100), "imgUpload", element);
    };
  });
});

layui.use(["form", "element"], function () {
  const form = layui.form;
  const layer = layui.form;
  const element = layui.element;
  form.on("submit(doTonguePre)", function () {
    $.ajax({
      type: "POST",
      url: "http://127.0.0.1:5000/tongue_pre",
      data: imgData,
      cache: false,
      processData: false,
      contentType: false,
      success: (res) => {
        $uploadUi.hide();
        res = JSON.parse(res);
        form.val("tonguePrediction", {
          tongueColor: res.tongue_color,
          coatingColor: res.coated_tongue_color,
        });
      },
      xhr: function () {
        $uploadUi.show();
        myXhr = $.ajaxSettings.xhr();
        if (myXhr.upload) {
          myXhr.upload.addEventListener(
            "progress",
            function (e) {
              if (e.lengthComputable) {
                showProgress(
                  Math.floor((e.loaded / e.total) * 100),
                  "upload",
                  element
                );
              }
            },
            false
          );
          myXhr.upload.addEventListener("load", () => {
            $uploadUi.hide();
            showProgress(0, "upload", element);
          });
        }
        return myXhr;
      },
    });
    return false;
  });
});

function addImg(
  {
    patient_info,
    encode,
    true_ton_color,
    pre_ton_color,
    true_coating_color,
    pre_coating_color,
  },
  idx
) {
  const isTonCorrect = true_ton_color === pre_ton_color;
  const isCoaCorrect = true_coating_color === pre_coating_color;
  // <img src=data:;base64,${encode}>
  patient_info = {
    ...patient_info,
    ...{
      true_ton_color,
      pre_ton_color,
      true_coating_color,
      pre_coating_color,
      isTonCorrect,
      isCoaCorrect,
    },
  };
  return [
    $(`
  <div class="component">
    <p style="text-align: center">${idx + 1}</p>
    <div class="upper">
    <img src=data:;base64,${encode}>
        
    </div>
    <div class="lower">
        <p class=${
          isTonCorrect ? "green" : "red"
        }>舌色(真实):<span>${true_ton_color}</span>&nbsp;&nbsp;&nbsp;舌色(预测):<span>${pre_ton_color}</span></p>
        <p class=${
          isCoaCorrect ? "green" : "red"
        }>苔色(真实):<span>${true_coating_color}</span>&nbsp;&nbsp;&nbsp;苔色(预测):<span>${pre_coating_color}</span></p>
    </div>
  </div> 
    `),
    isTonCorrect,
    isCoaCorrect,
    patient_info,
  ];
}

function bindShowPatientInfo(el, info) {
  layui.use(["table", "layer"], function () {
    const table = layui.table;
    const layer = layui.layer;
    el.on("click", () => {
      $(".ton_patient_detail").empty();
      let cols = [];
      let dealedInfo = info;
      if (Object.keys(dealedInfo).length !== 0) {
        $ton_patient_detail.append($(`<table class="patient_info"></table>`));
        switch (info.id?.[0]) {
          case "l": {
            dealLungData(dealedInfo);
            cols = lungCols;
            break;
          }
          case "k": {
            dealKindeyData(dealedInfo);
            cols = kidneyCols;
            break;
          }
          default: {
            dealLiverData(dealedInfo);
            cols = liverCols;
            break;
          }
        }
        setTimeout(() => {
          //使用计时器，防止表格渲染出现格式问题
          //根据data渲染病人的数据
          dealedInfo &&
            table.render({
              elem: ".patient_info", // 定位表格ID
              title: "详细信息",
              cols,
              data: [dealedInfo],
            });
        }, 0);
      } else {
        $(".ton_patient_detail").empty();
        $ton_patient_detail.append($(`<div class="no_data">数据暂无</div>`));
      }
      layer.open({
        type: 1,
        shadeClose: true,
        resize: false,
        area: "1000px",
        title: "详细信息",
        content: $(".ton_patient_detail"),
      });
    });
  });
}

function dealLungData(e) {
  e.sex = e.sex === "2" ? "女" : "男";
  e.Lung_qi_deficiency = e.Lung_qi_deficiency === "1" ? "是" : "否";
  e.spleen_qi_deficiency = e.spleen_qi_deficiency === "1" ? "是" : "否";
  e.kidney_qi_deficiency = e.kidney_qi_deficiency === "1" ? "是" : "否";
  e.PEF = e.PEF === "None" ? "无数据" : e.PEF;
}

function dealLiverData(e) {
  e.sex = e.sex === "1" ? "女" : "男";
  e.symptoms_type = e.symptoms_type === "1" ? "肝胆湿热症" : "肝郁脾虚症";
}

function dealKindeyData(e) {
  e.sex = e.sex === "2" ? "女" : "男";
  e.symptoms_type = e.symptoms_type === "1" ? "肾阳虚" : "肾阴虚";
}

layui.use(["form", "layer"], function () {
  const form = layui.form;
  const layer = layui.layer;
  form.on("select(tonBatchSelect)", function (data) {
    const { value } = data;
    let predictNum = parseInt(value, 10);
    layer.load(2);
    $.ajax({
      type: "POST", //请求的方法
      url: "http://127.0.0.1:5000/tongue_batch_pre",
      data: {
        num: predictNum,
      },
      success: (data) => {
        predictData = [];
        $batch_show.empty();
        data = JSON.parse(data);
        layer.closeAll();
        const { tongueData, tongue_color_accuracy, moss_color_accuracy } = data;
        form.val("tonBatchPre", {
          ton_acu: tongue_color_accuracy,
          moss_acu: moss_color_accuracy,
        });
        for (let i = 0; i < tongueData.length; ++i) {
          const [el, isTon, isCoa, patient_info] = addImg(tongueData[i], i);
          $batch_show.append(el);
          bindShowPatientInfo(el, patient_info);
          predictData.push([el, isTon, isCoa, patient_info]);
          switch (patient_info?.id?.[0]) {
            case "k":
              kidney_info.push(patient_info);
              break;
            case "l":
              lung_info.push(patient_info);
              break;
            case undefined:
              break;
            default:
              liver_info.push(patient_info);
              break;
          }
        }
        $classifyBtn.attr("disabled", false)
        $info.show();
        getTable(kidney_info, "kidney", undefined, 1);
        getTable(lung_info, "lung", undefined, 1);
        getTable(liver_info, "liver", undefined, 1);
      },
    });
  });
});

function getTable(postData, type, qObj = { page: 1, limit: 10 }, first = 0) {
  switch (type) {
    case "kidney":
      if (first) postData.forEach((e) => dealKindeyData(e));
      renderTable(postData, kidneyColsDetail, ".kidney_info_table", type, qObj);
      break;
    case "lung":
      if (first) postData.forEach((e) => dealLungData(e));
      renderTable(postData, lungColsDetail, ".lung_info_table", type, qObj);
      break;
    case "liver":
      if (first) postData.forEach((e) => dealLiverData(e));
      renderTable(postData, liverColsDetail, ".liver_info_table", type, qObj);
      break;
  }
}

function renderTable(postData, cols, el, type, qObj) {
  layui.use(["table"], function () {
    const table = layui.table;
    const { page, limit } = qObj;
    const data = postData.slice((page - 1) * limit, page * limit);
    table.render({
      elem: el, // 定位表格ID
      cols,
      data,
      limit: qObj.limit, // 每一页数据条数
      done: function (res) {
        // 分页组件
        let $el = null;
        switch (type) {
          case "kidney":
            $el = $(".kidney_info_table+div");
            break;
          case "lung":
            $el = $(".lung_info_table+div");
            break;
          case "liver":
            $el = $(".liver_info_table+div");
            break;
        }
        res.data.forEach((e, idx) => {
          const ton_color = e.isTonCorrect ? "green" : "red";
          const coa_color = e.isCoaCorrect ? "green" : "red";
          $el
            .find('tr[data-index="' + idx + '"]')
            .find('td[data-field="true_ton_color"]')
            .css("color", ton_color)
            .next()
            .css("color", ton_color)
            .next()
            .css("color", coa_color)
            .next()
            .css("color", coa_color);
        });
        getPage(qObj, postData, type, "page_" + type, postData.length);
      },
    });
  });
}

function getPage(queryObj, data, type, page_el, len) {
  layui.use(["laypage"], function () {
    const laypage = layui.laypage;
    // 设置分页
    laypage.render({
      elem: page_el, // 根据ID定位
      count: len, // 获取的数据总数
      limit: queryObj.limit, // 每页默认显示的数量，同上
      layout: ["prev", "page", "next", "limit", "skip"],
      curr: queryObj.page, // 页码
      jump: function (obj, first) {
        if (!first) {
          queryObj.page = obj.curr; // 设置当前页位置
          queryObj.limit = obj.limit; // 设置每页的数据条数
          getTable(data, type, queryObj);
        }
      },
    });
  });
}

function classify(idx) {
  $(".component").detach();
  $batch_show.empty();
  const $correct = $(`<div class="correct green"><p>预测正确</p></div>`);
  const $error = $(`<div class="error red"><p>预测不正确</p></div>`);
  for (let i = 0; i < predictData.length; ++i) {
    const [el, isTon, isCoa] = predictData[i];
    if (idx === 2) $batch_show.append(el);
    else if (idx === 0 ? isTon : isCoa) {
      $correct.append(el);
    } else {
      $error.append(el);
    }
  }
  if (idx !== 2) {
    $batch_show.append($correct).append($error);
  }
}

$(".accordTonColor").on("click", () => {
  classify(0);
});

$(".recovery").on("click", () => {
  classify(2);
});

$(".accordCoaColor").on("click", () => {
  classify(1);
});

const $showImg = $(".update_show img");
const $batch_show = $(".batch_show");
const $uploadUi = $(".uploadUi");
const $imgProgress = $(".update_show .imgProgress");
const $ton_patient_detail = $(".ton_patient_detail");
const $recovery = $(".recovery");
const $info = $(".info");
const $classifyBtn = $(".classify")
let predictData = [];
$uploadUi.hide();
let imgData = new FormData();

const kidney_info = [];
const liver_info = [];
const lung_info = [];
