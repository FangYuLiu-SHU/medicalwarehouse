const kidneyCols = [
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
  ],
];

const liverCols = [
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
    { field: "pulse", title: "脉", align: "center" }
  ],
];

const lungCols = [
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
      field: "Wesmedicine_diagnosis",
      title: "西医诊断",
      width: 160,
      align: "center",
    },
    {
      field: "Lung_qi_deficiency",
      title: "肺气虚",
      width: 80,
      align: "center",
    },
    { field: "spleen_qi_deficiency", title: "脾气虚", width: 80, align: "center" },
    { field: "kidney_qi_deficiency", title: "肾气虚", width: 80, align: "center" },
    { field: "FEV1", title: "FEV1", width: 100, align: "center" },
    { field: "FVC", title: "FVC", width: 100, align: "center" },
    { field: "FEV1%", title: "FEV1%", width: 100, align: "center" },
    { field: "FEV1/FVC", title: "FEV1/FVC", width: 100, align: "center" },
    { field: "PEF", title: "PEF", width: 100, align: "center" },
    { field: "tongue", title: "舌", width: 180, align: "center" },
    { field: "pulse", title: "脉",width: 80, align: "center" }
  ],
]

const increseItem = [{
  field: "true_ton_color",
  title: "舌色真实标签",
  width: 120,
  align: "center",
}, {
  field: "pre_ton_color",
  title: "舌色预测标签",
  width: 120,
  align: "center",
}, {
  field: "true_coating_color",
  title: "苔色真实标签",
  width: 120,
  align: "center",
}, {
  field: "true_coating_color",
  title: "苔色预测标签",
  width: 120,
  align: "center",
}]
const kidneyColsDetail = [[...kidneyCols[0].concat(increseItem)]]
const liverColsDetail = [[...liverCols[0].concat(increseItem)]]
const lungColsDetail = [[...lungCols[0].concat(increseItem)]]