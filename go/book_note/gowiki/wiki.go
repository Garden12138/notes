package main

import (
	"errors"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"regexp"
)

type Page struct {
	Title string
	Body []byte
}

var templates = template.Must(template.ParseFiles("view.html", "edit.html"))
var validPath = regexp.MustCompile("^/(edit|save|view)/([a-zA-Z0-9]+)$")

func main()  {
	// Data Structures example
	p1 := &Page{Title: "TestPage", Body: []byte("This is a simple Page.")}
	p1.save()
	p2,_ := loadPage("TestPage")
	fmt.Println(string(p2.Body))
	// Using net/http to serve wiki pages example
	http.HandleFunc("/view/", makeHandler(viewHandler))
	http.HandleFunc("/edit/", makeHandler(editHandler))
	http.HandleFunc("/save/", makeHandler(saveHandler))
	log.Fatal(http.ListenAndServe(":8080", nil))
}

func (p *Page) save() error {
	filename := p.Title + ".txt"
	return os.WriteFile(filename, p.Body, 0600)
}

func loadPage(title string) (*Page, error) {
	filename := title + ".txt"
	body, err := os.ReadFile(filename)
	if err != nil {
		return &Page{Title: "", Body: []byte("")}, err
	}
	return &Page{Title: title, Body: body}, nil
}

func viewHandler(rw http.ResponseWriter, r *http.Request, title string)  {
	//title, titleErr := getTitle(rw, r)
	//if titleErr != nil {
	//	return
	//}
	p, err := loadPage(title)
	if err != nil {
		http.Redirect(rw, r, "/edit/" + title, http.StatusFound)
		return
	}
	renderTemplate("view", rw, p)
}

func editHandler(rw http.ResponseWriter, r *http.Request, title string)  {
	//title, titleErr := getTitle(rw, r)
	//if titleErr != nil {
	//	return
	//}
	p, err := loadPage(title)
	if err != nil{
		p = &Page{Title: title}
	}
	renderTemplate("edit", rw, p)
}

func saveHandler(rw http.ResponseWriter, r *http.Request, title string)  {
	//title, titleErr := getTitle(rw, r)
	//if titleErr != nil {
	//	return
	//}
	body := r.FormValue("body")
	p := &Page{Title: title, Body: []byte(body)}
	err := p.save()
	if err != nil {
		http.Error(rw, err.Error(), http.StatusInternalServerError)
		return
	}
	http.Redirect(rw, r, "/view/" + title, http.StatusFound)
}

func renderTemplate(viewName string, rw http.ResponseWriter, p *Page)  {
	err := templates.ExecuteTemplate(rw, viewName + ".html", p)
	if err != nil {
		http.Error(rw, err.Error(), http.StatusInternalServerError)
	}
}

func getTitle(rw http.ResponseWriter, r *http.Request) (string, error) {
	m := validPath.FindStringSubmatch(r.URL.Path)
	if m == nil {
		http.NotFound(rw, r)
		return "", errors.New("invalid Page Title")
	}
	return m[2], nil
}

func makeHandler(fn func(http.ResponseWriter, *http.Request, string)) http.HandlerFunc {
	return func(rw http.ResponseWriter, r *http.Request) {
		m := validPath.FindStringSubmatch(r.URL.Path)
		if m == nil {
			http.NotFound(rw, r)
			return
		}
		fn(rw, r, m[2])
	}
}

