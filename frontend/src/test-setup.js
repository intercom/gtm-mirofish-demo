import { config } from '@vue/test-utils'
import { createPinia } from 'pinia'
import i18n from './i18n'

config.global.plugins.push(createPinia(), i18n)
