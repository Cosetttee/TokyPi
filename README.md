### TokyPi
**A reverse engineered user-friendly Python API for searching and downloading audiobooks books from TokyBook.**

### Usage Example

- **First Import** `from Tokipi import Search, Book`

1. **Search for Audiobooks:**

    ```python
    # Search for audiobooks
    search_query = "Harry Potter"  # Replace with your desired search query
    search = Search(search_query)
    search_results = search.results()

    # Print search results
    print("Search Results:")
    for idx, result in enumerate(search_results):
        print(f"{idx + 1}. Title: {result['book_title']}, Published: {result['date_published']}, Summary: {result['summary']}")
    ```

    Replace `"Harry Potter"` with your desired search query. It will print the search results including the title, publication date, and summary of each book.

2. **Download Single Episode:**

    ```python
    single_book_url = search_results[0]['link']  # Replace with the link of the book you want to download from the search results
    book = Book(single_book_url)
    book_episodes = book.episodes()
    if book_episodes:
        episode_to_download = book_episodes[0]  # Downloading the first episode from the book
        asyncio.run(book.download_episode(episode_to_download['name'], episode_to_download['url'], "./"))
    else:
        print("No episodes found for the selected book.")
    ```

    Replace `single_book_url` with the link of the book you want to download from the search results. It will download the first episode of the selected book.

3. **Download All Episodes of a Book:**

    ```python
    book_to_download_url = "BOOK LINK"
    book_to_download = Book(book_to_download_url)
    download_path = "./"  # Replace with your desired download path
    print(f"Downloading all episodes of the book to {download_path}")
    asyncio.run(book_to_download.download_episodes(download_path))
    ```

    Replace `book_to_download_url` with the link of the book you get from the search function.

4. **Print List of Episodes of a Book:**

    ```python
    print("List of episodes of the book:")
    for idx, episode in enumerate(book_to_download.episodes()):
        print(f"{idx + 1}. {episode['name']}")
    ```

    It will print the list of episodes of the selected book.
