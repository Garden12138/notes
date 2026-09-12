import { createApp } from "vue";
import {
  BackTop,
  Button,
  Card,
  Checkbox,
  Col,
  Collapse,
  ConfigProvider,
  DatePicker,
  Dropdown,
  Empty,
  Form,
  Input,
  InputNumber,
  Layout,
  Menu,
  Progress,
  Row,
  Select,
  Space,
  Tag,
} from "ant-design-vue";
import "ant-design-vue/dist/reset.css";

import App from "./App.vue";
import router from "./router";

const app = createApp(App).use(router);

[
  Button,
  Card,
  Checkbox,
  Col,
  Collapse,
  ConfigProvider,
  DatePicker,
  Dropdown,
  Empty,
  Form,
  Input,
  InputNumber,
  Layout,
  Menu,
  Progress,
  Row,
  Select,
  Space,
  Tag,
].forEach((component) => app.use(component));

app.component("ABackTop", BackTop);
app.mount("#app");
