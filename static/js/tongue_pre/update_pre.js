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

function addImg({
  patient_info,
  encode,
  true_ton_color,
  pre_ton_color,
  true_coating_color,
  pre_coating_color,
}) {
  const isTonCorrect = true_ton_color === pre_ton_color;
  const isCoaCorrect = true_coating_color === pre_coating_color;
  // <img src=data:;base64,${encode}>
  // <img src=${"C:/Users/Lenovo/Desktop/前端/京东商城/img/1.jpg"}>
  return [
    $(`
  <div class="component">
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
      $(".patient_detail").empty();
      let cols = [];
      let dealedInfo = info;
      if (Object.keys(dealedInfo).length !== 0) {
        $patient_detail.append($(`<table class="patient_info"></table>`));
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
        $(".patient_detail").empty();
        $patient_detail.append($(`<div class="no_data">数据暂无</div>`));
      }
      layer.open({
        type: 1,
        shadeClose: true,
        resize: false,
        area: "1000px",
        title: "详细信息",
        content: $(".patient_detail"),
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
          const [el, isTon, isCoa, patient_info] = addImg(tongueData[i]);
          $batch_show.append(el);
          bindShowPatientInfo(el, patient_info);
          predictData.push([el, isTon, isCoa, patient_info]);
        }
      },
    });
  });
});

function classify(idx) {
  $(".component").detach();
  const $correct = $(`<div class="correct"></div>`);
  const $error = $(`<div class="error"></div>`);
  for (let i = 0; i < predictData.length; ++i) {
    const [el, isTon, isCoa] = predictData[i];
    if(idx === 2) $batch_show.append(el);
    else if (idx === 0 ? isTon : isCoa) {
      $correct.append(el);
    } else {
      $error.append(el);
    }
  }
  if(idx !== 2) {
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
const $patient_detail = $(".patient_detail");
const $recovery = $(".recovery");
let predictData = [];
$uploadUi.hide();
let imgData = new FormData();
