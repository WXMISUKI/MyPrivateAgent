import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './assets/css/variables.css'
import './assets/css/base.css'
import './assets/css/animations.css'

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
