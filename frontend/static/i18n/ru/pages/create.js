export default {
  create: {
    title: 'Burning Message - Создать',
    subtitle: 'Безопасная и анонимная open-source платформа',
    features: {
      noHistory: 'Без истории',
      noTracking: 'Без отслеживания',
      noDatabase: 'Без базы данных'
    },
    messageInput: 'Введите ваше сообщение здесь...',
    createButton: 'Создать самоуничтожающееся сообщение',
    dropZoneText: 'Нажмите или перетащите изображение сюда',
    dropZoneHint: '1 изображение, макс. 3МБ',
    dropZoneFormat: '( jpg png gif webp )',
    useAccessToken: 'Использовать токен доступа',
    visible: 'Видимость',
    validity: 'Срок действия',
    tokenPlaceholder: 'Можно использовать запоминающуюся фразу~',
    tokenHintPlaceholder: 'Необязательная подсказка для токена\n\nнапр.: \'Наше любимое кафе\'',
    validation: {
      emptyCustomID: 'Пожалуйста, введите пользовательский ID сообщения.',
      emptyMessage: 'Пожалуйста, введите сообщение или добавьте изображения',
      emptyToken: 'Пожалуйста, введите пользовательский токен.',
      maxImages: 'Разрешено только {{count}} изображение. Пожалуйста, сначала удалите существующее',
      fileType: 'Тип файла {{type}} не поддерживается',
      fileSize: 'Размер файла превышает лимит в {{size}}МБ'
    },
    errors: {
      INVALID_EXPIRY: 'Выбрано недопустимое время истечения срока',
      INVALID_BURN: 'Выбрано недопустимое время чтения',
      INVALID_FONT: 'Выбран недопустимый размер шрифта',
      MAX_IMAGES_EXCEEDED: 'Разрешено только 1 изображение',
      INVALID_FILE_TYPE: 'Тип файла не поддерживается',
      FILE_TOO_LARGE: 'Размер файла превышает лимит в 3МБ',
      TOO_MANY_ATTEMPTS: 'Слишком много запросов. Пожалуйста, подождите немного',
      SERVER_ERROR: 'Ошибка сервера. Повторите попытку позже',
      createFailed: 'Не удалось создать сообщение. Повторите попытку',
      networkError: 'Ошибка сети. Повторите попытку позже',
      MESSAGE_ID_EXISTS: 'ID сообщения уже существует, выберите другой.'
    }
  }
} 