import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import { vuetify } from "./plugins/vuetify";
import "@fortawesome/fontawesome-free/css/all.css";
const app = createApp(App);

app.use(vuetify);
app.use(router);

app.mount("#app");
