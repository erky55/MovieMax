# MovieFlix

## Description
Watch Movies on switch

## Prerequisites

Make sure you have the following installed before running the project:

- Python 3.10

## Setup

1. Clone the repository:

    ```bash
    git clone https://github.com/erky55/movieflix.git
    cd movieflix
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the project root and add the following:

    ```env
    BOT_TOKEN=your_bot_token
    APP_ICON=https://f004.backblazeb2.com/file/switch-bucket/e78c287a-abc0-11ee-883b-d41b81d4a9ef.png
    SECONDARY_ICON=https://f004.backblazeb2.com/file/switch-bucket/6c0928da-abc3-11ee-82f3-d41b81d4a9ef.png
    ```

    Replace `your_bot_token` with the actual token for your bot.

## Usage

Run the bot using the following command:

```bash
python main.py
```

## Configuration

- `BOT_TOKEN`: Telegram bot token obtained from the BotFather.
- `APP_ICON`: URL for the main app icon.
- `SECONDARY_ICON`: URL for the secondary app icon.

## Contributing

If you'd like to contribute to the project, please follow the guidelines in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

---

Feel free to customize the README according to your project's specific needs. Include additional sections, such as "Features," "Troubleshooting," or any other relevant information.