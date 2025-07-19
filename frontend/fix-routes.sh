#!/bin/bash

# Fix all dynamic route parameters to use Promise<{ ... }>
find /home/sunwoo/yooni/frontend/app/api -name "route.ts" -path "*\[*\]*" | while read file; do
  echo "Fixing $file"
  
  # Fix GET method
  sed -i 's/{ params }: { params: { \([^}]*\) } }/context: { params: Promise<{ \1 }> }/g' "$file"
  
  # Fix POST method
  sed -i 's/,\s*{ params }: { params: { \([^}]*\) } }/, context: { params: Promise<{ \1 }> }/g' "$file"
  
  # Add await for params
  sed -i '/context: { params: Promise<{/,/^[[:space:]]*try {/ {
    /try {/a\    const params = await context.params;
  }' "$file"
  
  # Replace direct params usage with awaited params
  sed -i 's/params\.\([a-zA-Z_][a-zA-Z0-9_]*\)/params.\1/g' "$file"
done

echo "Done fixing routes"