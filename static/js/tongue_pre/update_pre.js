/*
layui.use("upload", function () {
  var upload = layui.upload;

  //执行实例
  var uploadInst = upload.render({
    elem: "#tongue_img", //绑定元素
    url: "http://127.0.0.1:5000/tongue_pre", //上传接口
    type: "POST",
    auto: false,
    bindAction: ".pre_btn button",
    choose: function (obj) {
      //obj参数包含的信息，跟 choose回调完全一致，可参见上文。
      obj.preview(function (index, file, result) {
        $(".update_show img").attr("src", result);
      });
    },
    done: function (res) {
      console.log(res);
    },
    error: function () {
      //请求异常回调
    },
  });
});
*/

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
        <img src=${encode}>
    </div>
    <div class="lower">
        <p>舌色(真实):<span>${true_ton_color}</span>&nbsp;&nbsp;&nbsp;舌色(预测):<span>${pre_ton_color}</span></p>
        <p>苔色(真实):<span>${true_coating_color}</span>&nbsp;&nbsp;&nbsp;苔色(预测):<span>${pre_coating_color}</span></p>
    </div>
  </div> 
    `);
}

layui.use("form", function () {
  var form = layui.form;
  form.on("select(tonBatchSelect)", function (data) {
    const { value } = data;
    let predictNum = parseInt(value, 10);
    $.ajax({
      type: "POST", //请求的方法
      url: "http://127.0.0.1:5000/tongue_batch_pre",
      data: {
        num: predictNum,
      },
      success: (data) => {
        $batch_show.empty();
        data = JSON.parse(data);
        for(let i = 0; i < data.length; ++i) {
            $batch_show.append(addImg(data[i]))
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
