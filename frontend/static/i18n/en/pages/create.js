export default {
  create: {
    subtitle: 'A secure, anonymous <a href="{{urls.opensource}}" class="hyperlink" target="_blank">open-source platform</a>',
    features: {
      noHistory: 'No history',
      noTracking: 'No tracking',
      noDatabase: 'No database'
    },
    messageInput: 'Type your message here...',
    createButton: 'Create Burning Message',
    dropZoneText: 'Click or drop image here to upload',
    dropZoneHint: '1 image, 3MB max',
    dropZoneFormat: '( jpg png gif webp )',
    useAccessToken: 'Use access token',
    visible: 'Visible',
    validity: 'Validity',
    tokenPlaceholder: '6~70 characters\n\na memorable line could be good~',
    tokenHintPlaceholder: 'Optional token hint\n\ne.g., \'Our favorite coffee shop\'',
    legal: 'By using this service, you agree to our <a href="{{urls.tos}}" class="hyperlink" target="_blank">Terms of Service</a> and <a href="{{urls.privacy}}" class="hyperlink" target="_blank">Privacy Policy</a>',
    validation: {
      emptyMessage: 'Please enter a message or add images',
      tokenLength: 'Password must be at least {{length}} characters',
      maxImages: 'Only {{count}} image allowed. Please remove the existing image first.',
      fileType: 'File type {{type}} not supported',
      fileSize: 'File size exceeds {{size}}MB limit'
    },
    errors: {
      INVALID_EXPIRY: 'Invalid expiry time selected',
      INVALID_BURN: 'Invalid burn time selected',
      INVALID_FONT: 'Invalid font size selected',
      MAX_IMAGES_EXCEEDED: 'Only 1 image allowed',
      INVALID_FILE_TYPE: 'File type not supported',
      FILE_TOO_LARGE: 'File size exceeds 3MB limit',
      TOO_MANY_ATTEMPTS: 'Too many requests. Please wait {{minutes}} minutes.',
      SERVER_ERROR: 'Server error. Please try again later.',
      createFailed: 'Failed to create message. Please try again.',
      networkError: 'Network error. Please try again later.',
      validationFailed: 'Validation failed:\n{{errors}}'
    }
  },
  urls: {
    tos: '/static/i18n/en/tos.html',
    privacy: '/static/i18n/en/privacy.html',
    opensource: 'https://github.com/ee2k/burning-message'
  }
}