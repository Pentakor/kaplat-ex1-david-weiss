// JavaScript to insert variable text
var variableText = "";
document.getElementById('variableText').innerHTML = variableText;
var varbookid = -1;
document.getElementById('varbookid').innerHTML = varbookid;

// JavaScript to handle form submission
document.getElementById('bookForm').addEventListener('submit', function(event) {
  event.preventDefault(); // Prevent the default form submission

  // Collect form data
  var title = document.getElementById('title').value;
  var author = document.getElementById('author').value;
  var year = document.getElementById('year').value;
  var price = document.getElementById('price').value;
  var genres = [];
  var checkboxes = document.querySelectorAll('input[name="genre"]:checked');
  checkboxes.forEach(function(checkbox) {
      genres.push(checkbox.value);
  });

  // Create the request body
  var requestBody = {
      "title": title,
      "author": author,
      "year": Number(year),
      "price": Number(price),
      "genres": genres
  };
  console.log(genres);
  // Send the POST request
  fetch('http://localhost:8574/book', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
  })
  .then(response => response.json())
  .then(data => {
      if (data.errorMessage) {
          alert(data.errorMessage);
      } else {
         console.log('Success',data);
          tablerefresh();
      }
  })
});


    // JavaScript to toggle dropdown visibility
    document.getElementById('dropdownButton').addEventListener('click', function() {
        var dropdownContent = document.getElementById('dropdownContent');
        if (dropdownContent.style.display === 'block') {
            dropdownContent.style.display = 'none';
        } else {
        dropdownContent.style.display = 'block';
        }
    });


// Function to update the book count
function deletebook(id) {
  fetch(`http://localhost:8574/book?id=${id}`, {
      method: 'DELETE'
  })
  .then(response => {
      if (!response.ok) {
          return response.json().then(errorData => {
              throw new Error(`Error ${response.status}: ${errorData.message}`);
          });
      }
      return response.json();
  })
  .then(data => {
      console.log('Book deleted:', data);
      // Refresh the table after successful deletion
      tablerefresh();
  })
  .catch(error => {
      console.error('Error:', error);
      alert(error.message);
  });
}

function tablecount() {
    fetch('http://localhost:8574/books/total')
        .then(response => response.json())
        .then(data => {
            document.getElementById('variableText').innerHTML = data.result;
        })
        .catch(error => alert(error));
}




var genreButton = document.getElementById('dropdownButton');
genreButton.addEventListener('click', ()=>dropdownrefresh('#dropdownContent','genre'));

// Function to refresh the table
function tablerefresh() {
    tablecount();
    fetch('http://localhost:8574/books')
        .then(response => response.json())
        .then(data => {
           createtable(data);

        })
        .catch(error => console.error('Error:', error));
}


// Add event listener to the refresh button
document.getElementById('refreshButton').addEventListener('click', tablerefresh);

window.onload = tablerefresh;

var modal = document.getElementById("myModal");

// Get the <span> element that closes the modal
var span = document.getElementsByClassName("close")[0];

var deleteButton = document.getElementById('deleteButton');

deleteButton.addEventListener('click', () => {
    deletebook(varbookid);
    modal.style.display = "none";
});



// When the user clicks on <span> (x), close the modal
span.onclick = function() {
  modal.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal) {
    modal.style.display = "none";
  }
}
  
document.getElementById('genreForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission
  
    // Collect form data
    var genre = document.getElementById('genre').value;
    genre = genre.toUpperCase();
  
    // Create the request body
    var requestBody = {
        "genre": genre
    };
    console.log(genre);
    // Send the POST request
    fetch('http://localhost:8574/genre', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        if (data.errorMessage) {
            alert(data.errorMessage);
        } else {
           console.log('Success',data);
        }
    })
    });

    document.getElementById('genreForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission
  
    // Collect form data
    var genre = document.getElementById('genre').value;
    genre = genre.toUpperCase();
  
    // Create the request body
    var requestBody = {
        "genre": genre
    };
    console.log(genre);
    // Send the POST request
    fetch('http://localhost:8574/genre', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(data => {
        if (data.errorMessage) {
            alert(data.errorMessage);
        } else {
           console.log('Success',data);
        }
    })
    });


document.getElementById('priceChangeForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission
  
    // Collect form data
    var price = document.getElementById('changeprice').value;
    price = Number(price);
    var bookid = document.getElementById('bookid').value;
  
    fetch(`http://localhost:8574/book?id=${bookid}&price=${price}`, {
        method: 'PUT'
    })
    .then(response => response.json())
    .then(data => {
        if (data.errorMessage) {
            alert(data.errorMessage);
        } else {
            console.log('Success', data);
            // Refresh the table after successful price change
            tablerefresh();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the price.');
    });
});


var genreButton = document.getElementById('genresFilter');
genreButton.addEventListener('click', ()=>dropdownrefresh('#genreDropdownContent','filteredgenre'));

document.getElementById('genresFilter').addEventListener('click', function() {
    var dropdownContent = document.getElementById('genreDropdownContent');
    if (dropdownContent.style.display === 'block') {
        dropdownContent.style.display = 'none';
    } else {
        dropdownContent.style.display = 'block';
    }
});



function dropdownrefresh(dropdownid,checkboxname) {
    fetch('http://localhost:8574/genre', {method: 'GET'})
        .then(response => response.json())
        .then(data=> {
            var dropdownContent = document.querySelector(dropdownid);
            dropdownContent.innerHTML = ''; // Clear existing rows
            if (data.errorMessage) {
                console.error('Error:', data.errorMessage);
                return;
            }
            data.result.forEach(genre => {
                var checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.name = checkboxname;
                checkbox.value = genre;
                dropdownContent.appendChild(checkbox);

                var label = document.createElement('label');
                label.textContent = genre;
                dropdownContent.appendChild(label);

                var br = document.createElement('br');
                dropdownContent.appendChild(br);
            });
        })
}

document.getElementById('filterForm').addEventListener('submit', function(event){
    event.preventDefault()
    var author = document.getElementById('filteredauthor').value.toLowerCase();
    var priceGreater = parseFloat(document.getElementById('priceGreater').value);
    var priceLess = parseFloat(document.getElementById('priceLess').value) ;
    var yearGreater = parseInt(document.getElementById('yearGreater').value) ;
    var yearLess = parseInt(document.getElementById('yearLess').value);
    var genres = [];
    var checkboxes = document.querySelectorAll('input[name="filteredgenre"]:checked');
    checkboxes.forEach(function(checkbox) {
      genres.push(checkbox.value);
    });
    console.log(author, priceGreater, priceLess, yearGreater, yearLess, genres);
    var httprequest= "http://localhost:8574/books?";
    if (author){
        httprequest += `author=${author}&`;
    }
    if (priceGreater){
        httprequest += `price-bigger-than=${priceGreater}&`;
    }
    if (priceLess){
        httprequest += `price-less-than=${priceLess}&`;
    }
    if (yearGreater){
        httprequest += `year-bigger-than=${yearGreater}&`;
    }
    if (yearLess){
        httprequest += `year-less-than=${yearLess}&`;
    }
    if (genres.length){
        httprequest += `genres=${genres.join(',')}`;
    }
    fetch(httprequest)
    .then(response => response.json()) // Convert the response to JSON
    .then(data => {
        createtable(data);

     })
     .catch(error => console.error('Error:', error));
});

function createtable(data)
{
    var booksTableBody = document.querySelector('#booksTable tbody');
    booksTableBody.innerHTML = ''; // Clear existing rows

    // Check if there is an error message
    if (data.errorMessage) {
        console.error('Error:', data.errorMessage);
        return;
    }

    // Iterate over the result array
    data.result.forEach(book => {
        var row = document.createElement('tr');

        var idCell = document.createElement('td');
        idCell.textContent = book.id;
        row.appendChild(idCell);
        
        var titleCell = document.createElement('td');
        titleCell.textContent = book.title;
        row.appendChild(titleCell);

        var authorCell = document.createElement('td');
        authorCell.textContent = book.author;
        row.appendChild(authorCell);

        var yearCell = document.createElement('td');
        yearCell.textContent = book.year;
        row.appendChild(yearCell);

        var priceCell = document.createElement('td');
        priceCell.textContent = book.price;
        row.appendChild(priceCell);

        var genresCell = document.createElement('td');
        genresCell.textContent = book.genres.join(', ');
        row.appendChild(genresCell);

      // Create the green button
      var buttonCell = document.createElement('td');
      var editButton = document.createElement('button');
      editButton.textContent = 'Delete';
      editButton.className = 'edit-button'; // Add the CSS class to the button

      editButton.addEventListener('click', () => {
        varbookid = book.id;
        document.getElementById('varbookid').innerHTML = varbookid;
        modal.style.display = "block";
      });

      buttonCell.appendChild(editButton);
      row.appendChild(buttonCell);
      booksTableBody.appendChild(row); 
      
    });
}