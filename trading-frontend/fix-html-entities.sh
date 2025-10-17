#!/bin/bash

# HTML 엔티티 이스케이핑 자동 수정 스크립트

# 따옴표 이스케이핑
find app components -name "*.tsx" -type f -exec sed -i "s/Don't/Don\&apos;t/g" {} \;
find app components -name "*.tsx" -type f -exec sed -i "s/can't/can\&apos;t/g" {} \;
find app components -name "*.tsx" -type f -exec sed -i "s/won't/won\&apos;t/g" {} \;
find app components -name "*.tsx" -type f -exec sed -i "s/hasn't/hasn\&apos;t/g" {} \;
find app components -name "*.tsx" -type f -exec sed -i "s/doesn't/doesn\&apos;t/g" {} \;
find app components -name "*.tsx" -type f -exec sed -i "s/isn't/isn\&apos;t/g" {} \;

echo "HTML entities fixed"
