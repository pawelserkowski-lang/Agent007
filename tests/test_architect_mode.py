import unittest

from core.architect import build_architect_response, detect_language, DetectionResult


class ArchitectModeTests(unittest.TestCase):
    def test_detect_python(self) -> None:
        code = """\
import os


def main():
    return 1
"""
        result = detect_language(code)
        self.assertEqual(result, DetectionResult(language="Python"))

    def test_detect_sql(self) -> None:
        code = "SELECT * FROM users WHERE id = 1;"
        result = detect_language(code)
        self.assertEqual(result.language, "SQL")

    def test_detects_framework_and_version(self) -> None:
        code = """\
from fastapi import FastAPI

app = FastAPI(version="1.1.0")
"""
        result = detect_language(code)
        self.assertEqual(result.language, "Python")
        self.assertEqual(result.framework, "FastAPI")
        self.assertEqual(result.version, "1.1.0")

    def test_plaintext_fallback(self) -> None:
        result = detect_language("Just a sentence without code.")
        self.assertEqual(result.language, "Plaintext")

    def test_build_response_includes_sections(self) -> None:
        code = "print('hello')"
        response = build_architect_response(code)
        self.assertIn("AUTO-DETEKCJA: Python", response)
        self.assertIn("DIAGNOZA:", response)
        self.assertIn("MODERNIZACJA I NAPRAWA", response)
        self.assertTrue(response.rstrip().endswith("print('hello')"))

    def test_detects_javascript_framework_and_semver(self) -> None:
        code = """\
import React from "react";
// react 18.2.0
export default function App() { return <div />; }
"""
        result = detect_language(code)
        self.assertEqual(result.language, "JavaScript")
        self.assertEqual(result.framework, "React")
        self.assertEqual(result.version, "18.2.0")

    def test_detects_go_and_gin(self) -> None:
        code = """\
package main

import (
    "fmt"
    "github.com/gin-gonic/gin"
)

// go1.22
func main() {
    r := gin.Default()
    fmt.Println(r)
}
"""
        result = detect_language(code)
        self.assertEqual(result.language, "Go")
        self.assertEqual(result.framework, "Gin")
        self.assertEqual(result.version, "1.22")

    def test_detects_php_and_laravel(self) -> None:
        code = """\
<?php

// php 8.2
use Illuminate\\Support\\Facades\\Route;

Route::get('/', function () {
    return 'ok';
});
"""
        result = detect_language(code)
        self.assertEqual(result.language, "PHP")
        self.assertEqual(result.framework, "Laravel")
        self.assertEqual(result.version, "8.2")

    def test_detects_ruby_and_rails(self) -> None:
        code = """\
# rails 7.1.3
class UsersController < ApplicationController
  def index
    render json: User.all
  end
end
"""
        result = detect_language(code)
        self.assertEqual(result.language, "Ruby")
        self.assertEqual(result.framework, "Rails")
        self.assertEqual(result.version, "7.1.3")

    def test_detects_rust_and_actix(self) -> None:
        code = """\
// rust 1.78.1
use actix_web::{get, web, App, HttpServer, Responder};

#[get("")]
async fn index() -> impl Responder {
    "ok"
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| App::new().route("/", web::get().to(index)))
        .bind(("0.0.0.0", 8080))?
        .run()
        .await
}
"""
        result = detect_language(code)
        self.assertEqual(result.language, "Rust")
        self.assertEqual(result.framework, "Actix")
        self.assertEqual(result.version, "1.78.1")

    def test_detects_cpp(self) -> None:
        code = """\
#include <iostream>

int main() {
    std::cout << "hello" << std::endl; // gcc 13.2
    return 0;
}
"""
        result = detect_language(code)
        self.assertEqual(result.language, "C++")
        self.assertIsNone(result.framework)
        self.assertEqual(result.version, "13.2")


if __name__ == "__main__":
    unittest.main()
