// Command apiface dumps the exported API surface of a Go package as TSV, using only go/parser and
// go/ast, for tools/symbol-coverage.py (S8.3).
//
//	go run . <dir-of-package>     # e.g. go run . ../../../tcell
//
// Output, one symbol per line, sorted, fields tab separated:
//
//	type	<owner>	<Name>	<doc-first-line>
//	func	<owner>	<Name>	<doc-first-line>
//	method	<RecvType>	<Name>	<doc-first-line>
//	var	-	<Name>	<doc-first-line>
//	const	-	<Name>	<doc-first-line>
//	subpkg	<relative/dir>	-	-
//
// The type/func/method/var/const rows are the root package's exported surface (the thing the wiki
// promises to document exactly once, PLAN.md 6.5). The subpkg rows let the Python side tell a real
// `pkg.Symbol` reference from an invented package name without downloading anything.
//
// Deliberately not go/types: no network, no module download, no build-tag solving. Names and doc
// comments are enough for a coverage report, and it works with a dirty or cross-tagged checkout.
package main

import (
	"bufio"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"unicode"
	"unicode/utf8"
)

type row struct {
	Kind  string
	Owner string
	Name  string
	Doc   string
}

func main() {
	// Resolution order: argument, $TCELL_DIR, then the sibling checkout of the wiki repo. The
	// sibling guess walks up to the marker file that only this repo has, because "../tcell" relative
	// to the process cwd was wrong when run from tools/apiface (it looked for tools/tcell).
	dir := os.Getenv("TCELL_DIR")
	if len(os.Args) > 1 {
		dir = os.Args[1]
	}
	if dir == "" {
		dir = filepath.Join(filepath.Dir(repoRoot()), "tcell")
	}
	if st, err := os.Stat(dir); err != nil || !st.IsDir() {
		fmt.Fprintf(os.Stderr, "apiface: no tcell checkout at %s - pass the path, set TCELL_DIR, or "+
			"check out the library beside the wiki repo (PLAN.md Prerequisites)\n", dir)
		os.Exit(2)
	}

	fset := token.NewFileSet()
	pkgs, err := parser.ParseDir(fset, dir, func(fi fs.FileInfo) bool {
		return !strings.HasSuffix(fi.Name(), "_test.go")
	}, parser.ParseComments)
	if err != nil {
		// Parse errors are not fatal for a name inventory; keep what we got.
		fmt.Fprintf(os.Stderr, "apiface: parse warnings: %v\n", err)
	}
	if len(pkgs) == 0 {
		fmt.Fprintf(os.Stderr, "apiface: no Go package found in %s\n", dir)
		os.Exit(2)
	}

	rows := []row{}
	add := func(kind, owner, name, doc string) {
		if name == "" || name == "_" || !exported(name) {
			return
		}
		rows = append(rows, row{Kind: kind, Owner: owner, Name: name, Doc: oneLine(doc)})
	}

	for pkgName, pkg := range pkgs {
		if strings.HasSuffix(pkgName, "_test") {
			continue
		}
		for _, file := range pkg.Files {
			for _, decl := range file.Decls {
				switch d := decl.(type) {
				case *ast.FuncDecl:
					if d.Recv != nil && len(d.Recv.List) == 1 {
						add("method", recvName(d.Recv.List[0].Type), d.Name.Name, d.Doc.Text())
					} else {
						add("func", "-", d.Name.Name, d.Doc.Text())
					}
				case *ast.GenDecl:
					for _, spec := range d.Specs {
						switch s := spec.(type) {
						case *ast.TypeSpec:
							add("type", "-", s.Name.Name, s.Doc.Text())
							if it, ok := s.Type.(*ast.InterfaceType); ok {
								for _, f := range it.Methods.List {
									for _, n := range f.Names {
										add("method", s.Name.Name, n.Name, f.Doc.Text())
									}
								}
							}
						case *ast.ValueSpec:
							kind := "var"
							if d.Tok == token.CONST {
								kind = "const"
							}
							for _, n := range s.Names {
								add(kind, "-", n.Name, s.Doc.Text())
							}
						}
					}
				}
			}
		}
	}

	for _, rel := range subpackages(dir) {
		rows = append(rows, row{Kind: "subpkg", Owner: rel, Name: "-", Doc: "-"})
	}

	sort.Slice(rows, func(i, j int) bool {
		if rows[i].Kind != rows[j].Kind {
			return rows[i].Kind < rows[j].Kind
		}
		if rows[i].Owner != rows[j].Owner {
			return rows[i].Owner < rows[j].Owner
		}
		return rows[i].Name < rows[j].Name
	})

	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	seen := map[row]bool{}
	for _, r := range rows {
		if seen[r] {
			continue
		}
		seen[r] = true
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\n", r.Kind, r.Owner, r.Name, r.Doc)
	}
}

func mergeFiles(pkgs map[string]*ast.Package) []*ast.File {
	var out []*ast.File
	for _, p := range pkgs {
		for _, f := range p.Files {
			out = append(out, f)
		}
	}
	return out
}

func exported(name string) bool {
	r, _ := utf8.DecodeRuneInString(name)
	return unicode.IsUpper(r)
}

func recvName(e ast.Expr) string {
	switch t := e.(type) {
	case *ast.StarExpr:
		return recvName(t.X)
	case *ast.IndexExpr: // generic receiver, e.g. (s *Foo[T])
		return recvName(t.X)
	case *ast.IndexListExpr:
		return recvName(t.X)
	case *ast.Ident:
		return t.Name
	}
	return "?"
}

func oneLine(s string) string {
	s = strings.TrimSpace(strings.ReplaceAll(s, "\n", " "))
	if i := strings.Index(s, "\t"); i >= 0 {
		s = s[:i]
	}
	if len(s) > 80 {
		s = s[:77] + "..."
	}
	return s
}

// repoRoot walks up from the working directory and from the executable looking for tools/pages.txt,
// the one file that identifies this repo as the Tcell wiki draft.
func repoRoot() string {
	wd, _ := os.Getwd()
	exe, _ := os.Executable()
	if real, err := filepath.EvalSymlinks(exe); err == nil {
		exe = real
	}
	for _, start := range []string{wd, exe} {
		for d := start; d != "" && d != "/"; d = filepath.Dir(d) {
			if _, err := os.Stat(filepath.Join(d, "tools", "pages.txt")); err == nil {
				return d
			}
		}
	}
	fmt.Fprintln(os.Stderr, "apiface: cannot find the wiki repo (no ancestor holds tools/pages.txt); "+
		"using the working directory, which is probably not what you want")
	return wd
}

func subpackages(root string) []string {
	var out []string
	clauses := token.NewFileSet() // package-clause-only parse, cheap and separate from the main fset
	_ = filepath.WalkDir(root, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		if !d.IsDir() {
			return nil
		}
		rel, _ := filepath.Rel(root, path)
		base := filepath.Base(path)
		if rel != "." && (strings.HasPrefix(base, ".") || strings.HasPrefix(base, "_") ||
			base == "testdata" || base == "vendor" || base == "gox") {
			return filepath.SkipDir
		}
		if rel == "." {
			return nil
		}
		entries, _ := os.ReadDir(path)
		var names []string
		for _, e := range entries {
			if !e.IsDir() && strings.HasSuffix(e.Name(), ".go") && !strings.HasSuffix(e.Name(), "_test.go") {
				names = append(names, filepath.Join(path, e.Name()))
			}
		}
		if len(names) == 0 {
			return nil
		}
		// A directory of `package main` programs is not importable, so it is not part of the API
		// surface a page can reference: demos/ holds eight of them (PLAN.md 7.5 lists the library
		// packages - color, sim, styles, lang, api/core, api/charset - not demos/hello).
		importable := false
		for _, name := range names {
			sf, err := parser.ParseFile(clauses, name, nil, parser.PackageClauseOnly)
			if err == nil && sf.Name != nil && sf.Name.Name != "main" {
				importable = true
				break
			}
		}
		if importable {
			out = append(out, filepath.ToSlash(rel))
		}
		return filepath.SkipDir
	})
	return out
}
