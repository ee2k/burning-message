export default {
  create: {
    title: 'Brennende Nachricht - Erstellen',
    header: 'Nachricht nach dem Lesen löschen',
    subtitle: 'Eine sichere, anonyme Open-Source-Plattform',
    features: {
      noHistory: 'Keine Historie',
      noTracking: 'Kein Tracking',
      noDatabase: 'Keine Datenbank'
    },
    messageInput: 'Geben Sie hier Ihre Nachricht ein...',
    createButton: 'Brennende Nachricht erstellen',
    dropZoneText: 'Klicken oder Bild hier ablegen',
    dropZoneHint: '1 Bild, maximal 3MB',
    dropZoneFormat: '( jpg png gif webp )',
    useCustomID: 'Benutzerdefinierte Nachrichten-ID verwenden',
    useAccessToken: 'Zugriffstoken verwenden',
    visible: 'Sichtbar',
    validity: 'Gültigkeit',
    tokenPlaceholder: 'Eine einprägsame Zeile könnte gut sein~',
    tokenHintPlaceholder: 'Optionaler Token-Hinweis\n\nz.B. \'Unser Lieblingscafé\'',
    validation: {
      emptyCustomID: 'Bitte geben Sie eine benutzerdefinierte Nachrichten-ID ein.',
      emptyMessage: 'Bitte geben Sie eine Nachricht ein oder fügen Sie Bilder hinzu',
      emptyToken: 'Bitte geben Sie einen benutzerdefinierten Token ein.',
      maxImages: 'Nur {{count}} Bild erlaubt. Bitte entfernen Sie zuerst das vorhandene Bild.',
      fileType: 'Dateityp {{type}} wird nicht unterstützt',
      fileSize: 'Dateigröße überschreitet {{size}}MB Limit'
    },
    errors: {
      INVALID_EXPIRY: 'Ungültige Ablaufzeit ausgewählt',
      INVALID_BURN: 'Ungültige Löschzeit ausgewählt',
      INVALID_FONT: 'Ungültige Schriftgröße ausgewählt',
      MAX_IMAGES_EXCEEDED: 'Nur 1 Bild erlaubt',
      INVALID_FILE_TYPE: 'Dateityp wird nicht unterstützt',
      FILE_TOO_LARGE: 'Dateigröße überschreitet 3MB Limit',
      TOO_MANY_ATTEMPTS: 'Zu viele Anfragen. Bitte warten Sie einen Moment.',
      SERVER_ERROR: 'Serverfehler. Bitte versuchen Sie es später erneut.',
      createFailed: 'Nachricht konnte nicht erstellt werden. Bitte versuchen Sie es erneut.',
      networkError: 'Netzwerkfehler. Bitte versuchen Sie es später erneut.',
      MESSAGE_ID_EXISTS: 'Nachrichten-ID existiert bereits, bitte wählen Sie eine andere.'
    }
  }
} 