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
      $showImg.hide()
      reads.onload = (e) => {
        $imgProgress.hide();
        $showImg.show();
        showProgress(0, "imgUpload", element);
        $showImg.attr("src", e.target.result);
      };
      reads.onprogress = e => {
        showProgress(Math.ceil((e.loaded / e.total) * 100), "imgUpload", element);
      }
    });

})

layui.use(["form","element"], function () {
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
                showProgress(Math.floor((e.loaded / e.total) * 100), "upload", element);
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
    encode,
    true_ton_color,
    pre_ton_color,
    true_coating_color,
    pre_coating_color
}) {
  return $(`
  <div class="component">
    <div class="upper">
        <img src=data:;base64,${encode}>
    </div>
    <div class="lower">
        <p>舌色(真实):<span>${true_ton_color}</span>&nbsp;&nbsp;&nbsp;舌色(预测):<span>${pre_ton_color}</span></p>
        <p>苔色(真实):<span>${true_coating_color}</span>&nbsp;&nbsp;&nbsp;苔色(预测):<span>${pre_coating_color}</span></p>
    </div>
  </div> 
    `);
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
        $batch_show.empty();
        data = JSON.parse(data);
        layer.closeAll()
        const { tongueData, tongue_color_accuracy, moss_color_accuracy} = data;
        form.val("tonBatchPre", {
          ton_acu: tongue_color_accuracy,
          moss_acu: moss_color_accuracy
        })
        for(let i = 0; i < tongueData.length; ++i) {
            $batch_show.append(addImg(tongueData[i]))
        }
      },
    });
  });
});

const $showImg = $(".update_show img");
const $batch_show = $(".batch_show");
const $uploadUi = $(".uploadUi");
const $imgProgress = $(".update_show .imgProgress")
$uploadUi.hide()
let imgData = new FormData();
